from django.conf.urls import url

from . import views

urlpatterns = [
    # 生成支付链接
    url(r'^payment/(?P<order_id>\d+)/$', views.PaymentView.as_view()),
    # 验证支付结果
    url(r'^payment/status/$', views.PaymentStatusView.as_view()),
]