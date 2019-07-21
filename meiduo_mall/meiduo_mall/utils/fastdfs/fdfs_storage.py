from django.core.files.storage import Storage


class FastDFSStorage(Storage):
    """自定义文件存储类"""

    def _open(self, name, mode='rb'):
        """
        当要打开文件时会调用此方法
        :param name: 要打开的文件名
        :param mode: 打开文件的模型 rb readb: 二进制只读
        """
        pass

    def _save(self, name, content):
        """
        当要上传文件时就会自动调用此方法
        :param name: 要上传的文件名
        :param content: 要上传的文件二制制数据 f = open() f.read()
        :return: file_id
        """
        pass

    def url(self, name):
        """
        当对图片字段调用url属性时就会自动调用此方法,来获取文件/图片的绝对路径
        :param name: 要访问的文件file_id
        :return: http://192.168.103.210:8888/ + name
        """
        return 'http://192.168.88.129:8888/' + name
