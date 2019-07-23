from django.conf.urls import url

from . import views

urlpatterns = [
    # 购物车
    url(r'^carts/$', views.CartsView.as_view(), name='carts'),
    # 全选购物车
    url(r'^carts/selection/$', views.CartsSelectAllView.as_view()),
    # 商品右上角购物车
    url(r'^carts/simple/$', views.CartsSimpleView.as_view(),name='info'),
]