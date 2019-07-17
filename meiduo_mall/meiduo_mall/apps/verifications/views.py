from django.views import View
from django_redis import get_redis_connection
from django.http import HttpResponse, JsonResponse
from random import randint
import logging

from meiduo_mall.libs.captcha.captcha import captcha
from celery_tasks.sms.tasks import send_sms_code
from meiduo_mall.utils.response_code import RETCODE
from . import constants

logger = logging.getLogger("django")


class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):
        """
        :param request: 请求对象
        :param uuid: 唯一标示图形验证码所属于的用户
        :return: image/jpg
        """
        # name:唯一标识； image_code_text：图形验证码的字符； image_bytes：图形验证码bytes
        name, image_code_text, image_bytes = captcha.generate_captcha()

        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        # 将图形验证码的字符存储到redis数据库中，用uuid当key
        redis_conn.setex("img_%s" % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, image_code_text)

        # 响应：把生成好的图形验证码bytes数据作为响应体响应给前端
        return HttpResponse(image_bytes, content_type="image/jpg")


class SMSCodesView(View):
    # 短信验证码

    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return: 响应结果
        """
        # 发短信之前先判断此手机号是否有没有在60秒内发送过
        # 创建redis连接对象
        redis_conn = get_redis_connection("verify_code")
        # 尝试去获取此手机发送过短信的标记
        send_flag = redis_conn.get("send_flag_%s" % mobile)
        # 如果有，提前响应
        if send_flag:
            return JsonResponse({
                "code": RETCODE.THROTTLINGERR,
                "errmsg": "短信发送过于频繁"
            })

        # 接收参数
        image_code = request.GET.get("image_code")
        uuid = request.GET.get("uuid")

        # 校验参数
        if not all([image_code, uuid]):
            return JsonResponse({
                "code": RETCODE.NECESSARYPARAMERR,
                "errmsg": "缺少必传参数"
            })

        # 提取图形验证码
        image_code_server = redis_conn.get("img_%s" % uuid)
        # 判断图形验证码是否过期或不存在
        if image_code_server is None:
            # 如果图形验证码过期或不存在
            return JsonResponse({
                "code": RETCODE.IMAGECODEERR,
                "errmsg": "图形验证码已失效"
            })

        # 如果图形验证码不为空，提取图形验证码之后在redis数据库中删除，避免恶意测试
        redis_conn.delete("img_%s" % uuid)

        # 对比图形验证码
        image_code_server = image_code_server.decode()  # bytes转字符串
        if image_code.lower() != image_code_server.lower():  # 转小写后比较
            return JsonResponse({
                "code": RETCODE.IMAGECODEERR,
                "errmsg": "输入图形验证码有误"
            })

        # 图形验证码对比正确，生成6位数短信验证码
        sms_code = "%06d" % randint(0, 999999)
        logger.info(sms_code)

        # 保存短信验证码
        # 创建redis管道
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 向redis中多存储一个此手机号已发送过短信验证码的标记，此标记有效时间60秒
        pl.setex("send_flag_%s" % mobile, constants.SMS_CODE_SEND_FLAG, 1)

        # 给当前注册账号的手机发送短信验证码
        # CCP().send_template_sms(要收短信的手机号, [短信验证码, 短信中提示的过期时间单位分钟], 短信模板id)
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
        # Celery异步发送短信验证码
        send_sms_code.delay(mobile, sms_code)

        # 响应结果
        return JsonResponse({"code": RETCODE.OK, "errmsg": "短信发送成功"})
