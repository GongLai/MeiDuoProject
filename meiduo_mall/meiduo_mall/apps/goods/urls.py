from django.conf.urls import url

from . import views

urlpatterns = [
    # 列表页展示
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view()),
    # 列表页热销排行
    url(r'^hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view()),

]