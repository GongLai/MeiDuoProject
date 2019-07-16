from django.shortcuts import render
from django.views import View


class IndexView(View):
    def get(self, request):
        """
        提供首页展示页面
        :param request:
        :return:
        """
        return render(request, 'index.html')
