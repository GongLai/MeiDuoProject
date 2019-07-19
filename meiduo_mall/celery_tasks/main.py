# celery启动文件
from celery import Celery

# 为celery使用django配置文件进行设置
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

# 创建celery实例
celery_app = Celery('meiduo')
# 加载celery配置,让生产者知道自己生产的任务存放到哪?
celery_app.config_from_object('celery_tasks.config')
# 自动注册celery任务(告诉生产者,它能生产什么样的任务)
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])
