"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^search/', include('haystack.urls')),  # 搜索模块

    url(r'^', include('users.urls', namespace='users')),  # 用户模块

    url(r'^', include('contents.urls', namespace='contents')),  # 首页模块

    url(r'^', include('verifications.urls', namespace='verifications')),  # 验证码模块

    url(r'^', include('oauth.urls', namespace='oauth')),  # QQ模块

    url(r'^', include('areas.urls', namespace='areas')),  # 省市区模块

    url(r'^', include('goods.urls', namespace='goods')),  # 商品模块
]
