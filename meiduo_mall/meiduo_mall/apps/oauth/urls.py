from django.conf.urls import url

from . import views

urlpatterns = [
    # 提供QQ登录url
    url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
    # QQ登录成功后的回调处理
    url(r'^oauth_callback/$', views.QQAuthUserView.as_view()),
]