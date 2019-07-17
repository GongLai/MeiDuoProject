from celery_tasks.sms.yuntongxun.sms import CCP
from celery_tasks.sms import constants
from celery_tasks.main import celery_app


# 只有用此装饰器装饰过的函数才能算得上是一个celery真正的任务  name：异步任务别名
@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    """
    发送短信异步任务
    :param mobile: 手机号
    :param sms_code: 短信验证码
    :return: 成功0 或 失败-1
    """
    # 给当前手机号发短信
    # CCP().send_template_sms(要收短信的手机号, [短信验证码, 短信中提示的过期时间单位分钟], 短信模板id)
    CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60],
                            constants.SEND_SMS_TEMPLATE_ID)
