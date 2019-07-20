from django.conf.urls import url

from . import views

urlpatterns = [
    # 用户注册
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    # 用户名重复校验
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
    # 手机号重复校验
    url(r'^mobiles/(?P<mobile>1[345789]\d{9})/count/$', views.MobileCountView.as_view()),
    # 用户登录
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    # 退出登录
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    # 用户中心
    url(r'^info/$', views.UserInfoView.as_view(), name='info'),
    # 添加邮箱
    url(r'^emails/$', views.EmailView.as_view(), name='emails'),
    # 邮箱激活
    url(r'^emails/verification/$', views.VerifyEmailView.as_view(), name='emails'),
    # 收货地址
    url(r'^addresses/$', views.AddressesView.as_view(), name='addresses'),
    # 新增收货地址
    url(r'^addresses/create/$', views.CreateAddressView.as_view(), name='create'),
    # 修改/删除收货地址
    url(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view()),


]