from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django import http
import re, json, logging
from django.contrib.auth import login, logout
from django_redis import get_redis_connection
from django.contrib.auth import authenticate
from django.contrib.auth import mixins

from .models import User, Address
from utils import constants
from utils.views import LoginRequiredView
from meiduo_mall.utils.response_code import RETCODE
from celery_tasks.email.tasks import send_verify_email
from .utils import generate_verify_email_url, check_verify_email_token

logger = logging.getLogger('django')


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
        response = redirect(request.GET.get('next', '/'))
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


class UserInfoView(LoginRequiredView):
    """用户中心"""

    def get(self, request):
        """用户中心展示"""

        return render(request, 'user_center_info.html')


class EmailView(LoginRequiredView):
    """添加邮箱"""

    def put(self, request):
        # 接收参数
        json_dict = json.loads(request.body)
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '缺少email参数'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({'code': RETCODE.EMAILERR, 'errmsg': '邮箱格式错误'})

        # 业务逻辑处理
        # 获取登录用户
        user = request.user
        # 修改email
        User.objects.filter(username=User.username, email='').update(email=email)

        # 发送邮件
        try:
            # 给当前登录用户的模型对象user的email字段赋值
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})

        # 异步发送验证邮件
        # 生成邮箱激活链接
        verify_url = generate_verify_email_url(user)
        # celery进行异步发送邮件
        send_verify_email.delay(email, verify_url)

        # 响应添加邮箱结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


class VerifyEmailView(LoginRequiredView):
    """验证邮件"""

    def get(self, request):
        # 获取数据
        token = request.GET.get('token')

        # 校验参数，判断token是否为空或过期，提前user
        if token is None:
            return http.HttpResponseBadRequest('缺少token')

        user = check_verify_email_token(token)
        if user is None:
            return http.HttpResponseForbidden('无效的token')

        # 修改email_active的值为True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('激活邮件失败')

        # 响应：返回激活邮件结果
        return redirect(reverse('users:info'))


class AddressesView(LoginRequiredView):

    def get(self, request):
        """提供收货地址界面展示"""

        # 1.获取用户收货地址列表
        user = request.user
        addresses_qs = Address.objects.filter(user=user, is_deleted=False)

        # 把查询集里面的模型转换成字典,然后再添加到列表中
        address_dict_list = []
        for address in addresses_qs:
            address_dict_list.append({
                'id': address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "province_id": address.province_id,
                "city": address.city.name,
                "city_id": address.city_id,
                "district": address.district.name,
                "district_id": address.district_id,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })

        context = {
            # 获取到用户默认收货地址的id
            'default_address_id': user.default_address_id,
            'addresses': address_dict_list,
        }

        return render(request, 'user_center_site.html', context)


class CreateAddressView(LoginRequiredView):
    """新增地址"""

    def post(self, request):
        # 判断当前用户所有未被逻辑删除的收货地址的数量:最多20个
        count = Address.objects.filter(user=request.user, is_deleted=False).count()
        if count > 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超过地址数量上限'})

        # 接收请求体 body数据
        json_dict = json.loads(request.body)
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 业务处理
        # 保持地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})

        # 新增地址成功，将新增的地址再转换成字典响应给前端实现局部刷新
        address_dict = {
            'id': address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "province_id": address.province_id,
            "city": address.city.name,
            "city_id": address.city_id,
            "district": address.district.name,
            "district_id": address.district_id,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


class UpdateDestroyAddressView(LoginRequiredView):
    """修改和删除收货地址"""

    def put(self, request, address_id):
        """
        修改收货地址
        :param request: 请求对象
        :param address_id: 要修改的地址id
        :return: 响应
        """
        # 1.接收参数
        json_dict = json.loads(request.body)
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2.校验参数
        # 校验参数
        if not all([title, receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 3.修改
        # 查询要修改的模型对象
        try:
            address_model = Address.objects.get(id=address_id, user=request.user, is_deleted=False)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')

        address_model.title = title
        address_model.receiver = receiver
        address_model.province_id = province_id
        address_model.city_id = city_id
        address_model.district_id = district_id
        address_model.place = place
        address_model.mobile = mobile
        address_model.tel = tel
        address_model.email = email
        address_model.save()
        # 如果使用update去修改数据时,auto_now 不会重新赋值
        # 如果是调用save做的修改数据,才会对auto_now 进行重新赋值

        # 4.把修改后的收货地址再转换成字典响应回去
        address_dict = {
            'id': address_model.id,
            'title': address_model.title,
            'receiver': address_model.receiver,
            'province_id': address_model.province_id,
            'province': address_model.province.name,
            'city_id': address_model.city_id,
            'city': address_model.city.name,
            'district_id': address_model.district_id,
            'district': address_model.district.name,
            'place': address_model.place,
            'mobile': address_model.mobile,
            'tel': address_model.tel,
            'email': address_model.email
        }

        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': '修改收货地址失败',
            'address': address_dict
        })

    def delete(self, request, address_id):
        """
        删除收货地址
        :param request: 请求对象
        :param address_id: 需要删除的地址id
        :return: 响应结果
        """
        try:  # 查询要删除的地址
            address = Address.objects.get(id=address_id)
            # 将需要删除的地址的逻辑删除设置为Ture
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})

        # 响应删除地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})
