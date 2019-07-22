from django.core.paginator import Paginator, EmptyPage
from django.views import View
from django.shortcuts import render
from django import http

from meiduo_mall.utils.response_code import RETCODE
from .models import GoodsCategory, SKU
from . import constants
from .utils import get_breadcrumb
from contents.utils import get_categories


class ListView(View):
    """商品列表页"""

    def get(self, request, category_id, page_num):
        """
        展示商品列表页
        :param request:
        :return:
        """
        # 判断category_id是否正确
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseNotFound('category_id不存在')

        # 接收sort参数：如果用户不传，就是默认的排序规则
        sort = request.GET.get('sort', 'default')

        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(category)

        # 按照排序规则查询给分类商品sku信息
        if sort == 'price':
            # 按照价格由低向高
            sort_field = 'price'
        elif sort == 'hot':
            # 按照销量由低向高
            sort_field = '-sales'
        else:
            # 'price'和'sales'以外的所有排序方式都归为'default'
            sort = 'default'
            sort_field = 'create_time'

        # 查询出指定类别下的所有商品
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(sort_field)

        # 创建分页器对象: Paginator(要分页的所有数据, 指定每页显示多少条数据)
        paginator = Paginator(skus, constants.GOODS_LIST_LIMIT)
        # 获取每页商品数据
        try:
            # 获取到指定页中的所有数据
            page_skus = paginator.page(page_num)
        except EmptyPage:
            # 如果page_num不正确，默认给用户404
            return http.HttpResponseNotFound('empty page')
        # 获取列表页总页数
        total_page = paginator.num_pages

        # 渲染页面
        context = {
            'categories': categories,  # 频道分类
            'breadcrumb': breadcrumb,  # 面包屑导航
            'sort': sort,  # 排序字段
            'category': category,  # 第三级分类
            'page_skus': page_skus,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }

        return render(request, 'list.html', context)


class HotGoodsView(View):
    """商品热销排序"""

    def get(self, request, category_id):

        # 校验
        try:
            cat3 = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')

        # 查询指定三级类型下的销售最高的前两个sku
        sku_qs = cat3.sku_set.filter(is_launched=True).order_by('-sales')[:2]
        # 模型转字典
        sku_list = []  # 用来装两个sku字典
        for sku_model in sku_qs:
            sku_list.append(
                {
                    'id': sku_model.id,
                    'price': sku_model.price,
                    'name': sku_model.name,
                    'default_image_url': sku_model.default_image.url
                }
            )

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': sku_list})
