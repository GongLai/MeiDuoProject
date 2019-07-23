from django.conf.urls import url

from . import views

urlpatterns = [
    # 提交订单
    url(r'^orders/settlement/$', views.OrderView.as_view()),
    # 订单结算
    url(r'^orders/commit/$', views.OrderCommitView.as_view()),
    # 提交成功后界面
    url(r'^orders/success/$', views.OrderSuccessView.as_view()),
]