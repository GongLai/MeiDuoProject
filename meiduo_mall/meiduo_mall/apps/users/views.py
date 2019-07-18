from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django import http
import re
from django.contrib.auth import login, logout
from django_redis import get_redis_connection
from django.contrib.auth import authenticate

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
        # 2.1 非空验证
        if not all([username, password, password2, mobile, sms_code, allow]):
            return http.HttpResponseForbidden("传入数据不完整")

        # 2.2 用户名
        if not re.match('^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('用户名为5-20个字符')
        if User.objects.filter(username=username).count() > 0:
            return http.HttpResponseForbidden('用户名已经存在')
        # 2.3 密码
        if not re.match('^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码为8-20个字符')
        # 2.4 确认密码
        if password != password2:
            return http.HttpResponseForbidden('两个密码不一致')
        # 2.5 手机号
        if not re.match('^1[3456789]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号错误')
        if User.objects.filter(mobile=mobile).count() > 0:
            return http.HttpResponseForbidden('手机号存在')
        # 2.6 短信验证码
        # 2.6.1 创建redis连接对象
        redis_conn = get_redis_connection("verify_code")
        # 2.6.2 获取redis中短信验证码
        sms_code_server = redis_conn.get("sms_%s" % mobile)

        # 2.6.3 判断短信验证码是否过期
        if sms_code_server is None:
            return http.HttpResponseForbidden({
                "code": RETCODE.SMSCODERR,
                "errmsg": "短信验证码已过期"
            })

        # 2.6.4 如果短信验证码存在，删除redis中存储的短信验证码【目的：一个短信验证码只能使用一次】
        redis_conn.delete("sms_%s" % mobile)
        # 2.6.5 redis短信验证码由bytes转为字符串类型
        sms_code_server = sms_code_server.decode()

        # 2.6.6 对比短信验证码
        if sms_code_server != sms_code:
            return http.HttpResponseForbidden({
                "code": RETCODE.SMSCODERR,
                "errmsg": "请输入正确的短信验证码"
            })

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


class LoginView(View):
    """用户登录"""

    def get(self, request):
        """
        展示登录页面
        :param request: 请求对象
        :return: 登录页面
        """
        return render(request, 'login.html')

    def post(self, request):
        """
        用户登录功能实现
        :param request: 请求对象
        :return: 响应结果
        """
        #  1.接受参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        #  2.校验参数
        # 登录认证
        user = authenticate(username=username, password=password)

        #  3.业务处理
        #  3.1 如果if成立说明登录失败
        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})
        #  3.2 实现状态保持
        login(request, user)
        #  3.3 设置状态保持的周期，判断用户是否勾选记住用户
        if remembered is None:
            # 没有选择记住用户，浏览器会话结束就过期，默认过期时间是两周
            # cookie如果指定过期时间为None 关闭浏览器删除, 如果指定0,它还没出生就没了
            request.session.set_expiry(0)

        #  4.响应
        response = redirect(reverse('homepag:index'))
        response.set_cookie('username', user.username, max_age=constants.USERNAME_COOKIE_EXPIRES)
        return response


class LogoutView(View):
    """退出登录"""

    def get(self, request):
        """
        实现退出登录逻辑
        :param request: 请求对象
        :return: 响应结果
        """
        # 清理session
        logout(request)
        # 退出登录，重定向回登录页
        response = redirect(reverse('users:login'))
        # 退出登录时清除
        response.delete_cookie('username')

        return response
