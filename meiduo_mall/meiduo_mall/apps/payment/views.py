from django.shortcuts import render
from alipay import AliPay
from django import http
from django.conf import settings
import os
from django.views import View

from utils.views import LoginRequiredView
from orders.models import OrderInfo
from meiduo_mall.utils.response_code import RETCODE
from .models import Payment


class PaymentView(LoginRequiredView):
    """生成支付链接"""

    def get(self, request, order_id):

        # 校验
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=request.user,
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单有误')

        # 支付宝
        # ALIPAY_APPID = '2016091900551154'
        # ALIPAY_DEBUG = True  # 表示是沙箱环境还是真实支付环境
        # ALIPAY_URL = 'https://openapi.alipaydev.com/gateway.do'
        # ALIPAY_RETURN_URL = 'http://www.meiduo.site:8000/payment/status/'
        # 创建AliPay支付宝对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,  # 应用的id
            app_notify_url=None,  # 默认回调url
            # /User/chao/Desktop/mei_27/mei/mei/apps/payment/keys/appxxx
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # 加密方式一定要和支付宝上设置的一致
            debug=settings.ALIPAY_DEBUG  # 如果是沙箱环境就设置为True,真实环境就设置False
        )

        # 调用它里面api_alipay_trade_page_pay方法得到登录链接后面的查询参数部分
        # 手机网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 要支付的订单编号
            total_amount=str(order.total_amount),  # 不能直接用Decimal类型需要转成字符串
            subject='美多商城:%s' % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )

        # 拼接好支付宝登录url
        # alipay_url = https://openapi.alipay.com/gateway.do? + order_string  # 真实环境
        # alipay_url = https://openapi.alipaydev.com/gateway.do? + order_string  # 沙箱环境
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})


class PaymentStatusView(View):
    """验证支付结果"""

    def get(self, request):
        # 获取查询参数
        query_dict = request.GET
        # 将QueryDict类型转换成字典
        data = query_dict.dict()
        # 再将字典中的sign移除
        sign = data.pop('sign')

        # 创建alipay支付宝对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,  # 应用的id
            app_notify_url=None,  # 默认回调url
            # /User/chao/Desktop/mei_27/mei/mei/apps/payment/keys/appxxx
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # 加密方式一定要和支付宝上设置的一致
            debug=settings.ALIPAY_DEBUG  # 如果是沙箱环境就设置为True,真实环境就设置False
        )

        # 调用verify方法进行对支付结果验证
        success = alipay.verify(data, sign)
        if success:  # 成功说明验证通过
            # 获取支付宝交易号
            trade_id = data.get('trade_no')
            # 获取美多订单编号
            order_id = data.get('out_trade_no')
            try:
                Payment.objects.get(trade_id=trade_id, order_id=order_id)
            except Payment.DoesNotExist:
                # 保存支付宝交易号及订单编号
                Payment.objects.create(
                    trade_id=trade_id,
                    order_id=order_id
                )
            # 修改订单状态
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
            # 响应
            return render(request, 'pay_success.html', {'trade_id': trade_id})
        else:
            return http.HttpResponseForbidden('非法请求')
