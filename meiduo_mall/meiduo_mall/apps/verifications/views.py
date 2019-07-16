from django.views import View
from django_redis import get_redis_connection
from django.http import HttpResponse

from meiduo_mall.libs.captcha.captcha import captcha
from . import constants


class ImageCodeView(View):
    """图型验证码"""
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
