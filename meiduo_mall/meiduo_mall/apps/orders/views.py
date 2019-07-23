from django.shortcuts import render
from django_redis import get_redis_connection
from decimal import Decimal
import json, logging
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.db import transaction

from meiduo_mall.utils.response_code import RETCODE
from .models import OrderInfo, OrderGoods
from goods.models import SKU
from users.models import Address
from utils.views import LoginRequiredView

logger = logging.error('django')


class OrderView(LoginRequiredView):
    """订单结算"""

    def get(self, request):
        """
        订单结算页面展示
        :param request:
        :return:
        """
        # 获取登录用户
        user = request.user
        # 查询地址信息
        try:
            addresses = Address.objects.filter(user=request.user, is_deleted=False)
        except Address.DoesNotExist:
            # 如果地址为空，渲染模板时会判断，并跳转到地址编辑页面
            addresses = None

        # 从Redis购物车中查询出被勾选的商品信息
        redis_conn = get_redis_connection('carts')
        redis_cart = redis_conn.hgetall('carts_%s' % user.id)
        cart_selected = redis_conn.smembers('selected_%s' % user.id)
        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(redis_cart[sku_id])

        # 准备初始值
        total_count = 0
        total_amount = Decimal(0.00)
        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]
            sku.amount = sku.count * sku.price
            # 计算总数量和总金额
            total_count += sku.count
            total_amount += sku.count * sku.price
        # 补充运费
        freight = Decimal('10.00')

        # 渲染界面
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight
        }

        return render(request, 'place_order.html', context)


class OrderCommitView(LoginRequiredView):
    """提交订单"""

    def post(self, request):
        # 接收请求体数据
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')  # 收货地址id,
        pay_method = json_dict.get('pay_method')  # 用户选择的支付方式
        user = request.user  # 获取当前登录用户对象
        # 校验
        if all([address_id, pay_method]) is False:
            return HttpResponseForbidden('缺少必传参数')

        try:
            address = Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            return HttpResponseForbidden('address_id有误')
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            # if pay_method not in OrderInfo.PAY_METHODS_ENUM.values():
            return HttpResponseForbidden('支付方式有误')

        # 生成订单编号: 时间 + 用户id  20190627091620000000001
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id

        # 根据支付方法判断订单状态
        # status = '待支付' if '支付方式如果是 支付宝支付' else '待发货'
        status = (OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                  if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']
                  else OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

        # 手动开启一个事务
        with transaction.atomic():

            # 创建事务保存点
            save_point = transaction.savepoint()
            try:
                # 保存订单基本信息记录  OrderInfo记录（一）
                order_model = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address_id=address_id,
                    total_count=0,
                    total_amount=Decimal('0.00'),  # 用来存储金钱,尽量用Decimal,在Decimal里面的数据必须用字符串
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=status
                )

                # 创建redis连接对象
                redis_conn = get_redis_connection('carts')
                # 获取redis中hash和set集合的购物车数据
                redis_carts = redis_conn.hgetall('carts_%s' % user.id)
                selected_ids = redis_conn.smembers('selected_%s' % user.id)

                # 将redis购物车数据过滤,只要那些勾选商品的sku_id和count
                cart_dict = {}  # 包装要购买的商品 {sku_id: count}
                for sku_id_bytes in selected_ids:
                    cart_dict[int(sku_id_bytes)] = int(redis_carts[sku_id_bytes])
                # 注意sku模型不能一次全部查询出来,会有缓存

                # 遍历要购物车商品的字典,开始对每个sku进行判断库存
                for sku_id in cart_dict:

                    while True:
                        # 获取到对应的sku模型
                        sku = SKU.objects.get(id=sku_id)
                        # 获取当前商品要购物车的数量
                        buy_count = cart_dict[sku_id]

                        # 获取当前sku原本的库存
                        origin_stock = sku.stock
                        # 获取当前sku原本的销量
                        origin_sales = sku.sales
                        # 没法避免脏读,但必须要解决脏写
                        # import time
                        # time.sleep(5)
                        # 判断库存
                        # 如果当前商品要购买的数量大于的它的库存,是不能下单
                        if buy_count > origin_stock:
                            # 库存不足事务中的操作进行回滚
                            transaction.savepoint_rollback(save_point)

                            return JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})

                        # 计算sku的新库存和销量
                        new_stock = origin_stock - buy_count
                        new_sales = origin_sales + buy_count
                        # 修改sku的库存和销量
                        # sku.stock = new_stock
                        # sku.sales = new_sales
                        # sku.save()
                        # 使用乐观锁来修改sku的库存和销量
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                          sales=new_sales)
                        # 如果返回0说明修改失败,说明有抢夺
                        if result == 0:
                            continue

                        # 修改spu的销量
                        spu = sku.spu
                        spu.sales += buy_count
                        spu.save()

                        # 保存订单中商品记录 OrderGoods记录 （多）
                        OrderGoods.objects.create(
                            order_id=order_id,
                            sku=sku,
                            count=buy_count,
                            price=sku.price
                        )

                        # 修改订单中购买商品总数量和总价
                        order_model.total_count += buy_count
                        order_model.total_amount += (sku.price * buy_count)

                        break  # 本商品下单成功后结束死循环
                    # 累加运费一定要放在for的外面,只算一次运费
                order_model.total_amount += order_model.freight
                order_model.save()
            except Exception as e:
                logger.error(e)
                # 暴力回滚
                transaction.savepoint_rollback(save_point)
                # 此处必须要提前响应
                return JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '下单失败'})
            else:
                # 提交事务
                transaction.savepoint_commit(save_point)

        # 删除购物车中已经购买过的商品
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s' % user.id, *selected_ids)
        pl.delete('selected_%s' % user.id)
        pl.execute()
        # 响应订单编号
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order_id': order_id})


class OrderSuccessView(LoginRequiredView):
    """提交订单成功后的界面"""

    def get(self, request):
        # 获取查询参数中的数据
        query_dict = request.GET
        order_id = query_dict.get('order_id')
        payment_amount = query_dict.get('payment_amount')
        pay_method = query_dict.get('pay_method')

        # 校验
        try:
            OrderInfo.objects.get(order_id=order_id, total_amount=payment_amount, pay_method=pay_method,
                                  user=request.user)
        except OrderInfo.DoesNotExist:
            return HttpResponseForbidden('订单有误')

        # 包装要拿到模板要进行渲染的数据
        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }

        return render(request, 'order_success.html', context)
