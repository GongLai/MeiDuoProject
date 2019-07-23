from django.shortcuts import render, redirect
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseServerError
import logging, re
from django_redis import get_redis_connection
from django.contrib.auth import login

from meiduo_mall.utils.response_code import RETCODE
from .models import OAuthQQUser
from .utils import generate_openid_signature, check_openid_signature
from users.models import User
from carts.utils import merge_cart_cookie_to_redis

logger = logging.getLogger('django')


class QQAuthURLView(View):
    """提供QQ登录url"""

    def get(self, request):
        # 获取查询参数next
        next = request.GET.get('next', '/')

        # 创建OAuthQQ实例对象，并给实例属性赋值
        # auth_qq = OAuthQQ(client_id='app_id', client_secret='app_key', redirect_uri='QQ登录成功后的回调url', state='标识')
        oauth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                           client_secret=settings.QQ_CLIENT_SECRET,
                           redirect_uri=settings.QQ_REDIRECT_URI,
                           state=next)

        # 调用它里面的get_qq_url方法得到拼接好的QQ登录url
        login_url = oauth_qq.get_qq_url()

        # 响应json
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


class QQAuthUserView(View):
    """用户扫码登录的回调处理"""

    def get(self, request):
        """Oauth2.0认证"""

        # 接收Authorization Code
        code = request.GET.get('code')
        # 校验code
        if code is None:
            return HttpResponseForbidden('缺少code参数')

        # 创建QQ登录SDK对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 调用SKD中get_access_token方法传入code获取access_token
            access_token = oauth.get_access_token(code)

            # 调用SKD中get_open_id方法传入access_token获取openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError('OAuth2.0认证失败')

        """拿到openid的后续绑定或登录处理"""
        try:
            # 使用openid查询 tb_oauth_qq表
            oauth_model = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果查询不到openid,说明此QQ号是第一次来登录美多商城,应用和一个美多用户进行绑定操作
            # 把openid进行加密,加密后渲染给模板,让前端界面帮我们暂存一会openid,以备后续绑定用户时使用
            openid = generate_openid_signature(openid)
            return render(request, 'oauth_callback.html', {'openid': openid})

        else:
            # 如果查询到openid,说明此QQ已绑定过美多用户,那么直接就登录成功
            user = oauth_model.user
            # 状态操持
            login(request, user)
            # 重定向到来源界面
            response = redirect(request.GET.get('state', '/'))
            # 在cookie中存储username
            response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)

            # QQ不是首次登录,登录成功那一刻合并购物车
            merge_cart_cookie_to_redis(request, response)
            # 响应
            return response

    def post(self, request):
        """绑定用户处理"""

        # 接收表单数据, mobile, pwd, sms_code, openid
        query_dict = request.POST
        mobile = query_dict.get('mobile')
        password = query_dict.get('password')
        sms_code = query_dict.get('sms_code')
        openid_sign = query_dict.get('openid')

        # 校验
        if all([mobile, password, sms_code, openid_sign]) is False:
            return HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('请输入正确的手机号码')
        # 短信验证码后期补充它的验证
        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        # 获取reids中短信验证码
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        # 判断验证码是否过期
        if sms_code_server is None:
            return HttpResponseForbidden('短信验证码已过期')
        # 删除reids中已被使用过的短信验证
        redis_conn.delete('sms_%s' % mobile)
        # 由bytes转换为str
        sms_code_server = sms_code_server.decode()
        # 判断用户输入的短信验证码是否正确
        if sms_code != sms_code_server:
            return HttpResponseForbidden('请输入正确的短信验证码')

        # 对openid进行解密
        openid = check_openid_signature(openid_sign)
        if openid is None:
            return HttpResponseForbidden('openid无效')

        try:
            # 查询当前手机号
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果查询不到,说明是没有注册过的用户,就创建一个新美多用户, 再和openid绑定
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
            pass
        else:
            # 如果查询到,说明是已注册用户,校验旧用户的密码是否正确那么openid就和已注册用户直接绑定
            if user.check_password(password) is False:
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或密码错误'})

        # 无论新老用户,都放心大胆的和openid进行绑定
        OAuthQQUser.objects.create(openid=openid, user=user)

        # 状态操持
        login(request, user)
        # 创建响应对象
        response = redirect(request.GET.get('state', '/'))
        # cookie中存储username
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
        # QQ用户首次登录[合并购物车]
        merge_cart_cookie_to_redis(request, response)
        # 重定向
        return response
