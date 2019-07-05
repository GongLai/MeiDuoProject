from django.conf.urls import url

from . import views

urlpatterns = [
    # 注册页面
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
   
]