from django.shortcuts import render
from django.views import View

from goods.models import ContentCategory
from contents.utils import get_categories


class IndexView(View):
    def get(self, request):
        """
        提供首页展示页面
        :param request:
        :return:
        """

        # 广告数据
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        # 渲染模板的上下文
        context = {
            'categories': get_categories(),
            'contents': contents,
        }

        return render(request, 'index.html', context)
