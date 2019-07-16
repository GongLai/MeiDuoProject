from django.shortcuts import render, redirect
from django.views import View
from django import http
import re
from django.contrib.auth import login, logout

from .models import User
from utils import constants
from meiduo_mall.utils.response_code import RETCODE


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供用户注册页面
        :param request: 请求对象
        :return: 用户注册页面
        """
        return render(request, 'register.html')

    def post(self, request):
        """
        用户注册实现
        :param request:
        :return:
        """
        # 1.接受参数
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        mobile = request.POST.get("mobile")
        sms_code = request.POST.get("sms_code")
        allow = request.POST.get("allow")

        # 2.数据校验
        # 2.1.非空验证
        if not all([username, password, password2, mobile, sms_code, allow]):
            return http.HttpResponseForbidden("传入数据不完整")

        # 2.2.用户名
        if not re.match('^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('用户名为5-20个字符')
        if User.objects.filter(username=username).count() > 0:
            return http.HttpResponseForbidden('用户名已经存在')
        # 2.3密码
        if not re.match('^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码为8-20个字符')
        # 2.4确认密码
        if password != password2:
            return http.HttpResponseForbidden('两个密码不一致')
        # 2.5手机号
        if not re.match('^1[3456789]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号错误')
        if User.objects.filter(mobile=mobile).count() > 0:
            return http.HttpResponseForbidden('手机号存在')

        # 3.业务处理
        # 1.创建用户对象
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                mobile=mobile
            )

        except:
            return render(request, 'register.html', {"register_errmsg": "注册失败"})

        # 2.状态保持
        login(request, user)

        # 向cookie中写用户名，用于客户端显示
        response = redirect('/')
        response.set_cookie('username', username, max_age=constants.USERNAME_COOKIE_EXPIRES)

        # 4.响应
        return response


class UsernameCountView(View):

    def get(self, request, username):
        """
        用户名重复注册校验
        :param request: 请求对象
        :param username: 用户名
        :return: JSON
        """
        # 使用username查询user表, 得到username的数量
        count = User.objects.filter(username=username).count()
        # 响应
        return http.JsonResponse({
            "code": RETCODE.OK,
            "errmsg": "OK",
            "count": count,
        })


class MobileCountView(View):

    def get(self, request, mobile):
        """
        手机号重复注册校验
        :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        # 使用username查询user表, 得到mobile的数量
        count = User.objects.filter(mobile=mobile).count()
        # 响应
        return http.JsonResponse({
            "code": RETCODE.OK,
            "errmsg": "OK",
            "count": count,
        })
