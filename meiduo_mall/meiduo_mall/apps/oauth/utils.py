from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings


def generate_openid_signature(openid):
    """对openid进行加密,并返回加密后的openid"""
    # 创建加密对象
    serializer = Serializer(settings.SECRET_KEY, 600)
    # 包装加密数据
    data = {'openid': openid}
    # 调用它的dumps方法,需要将加密的数据包装成字典格式, 加密后返回bytes
    openid_sign_bytes = serializer.dumps(data)

    # 返回加密后的openid
    return openid_sign_bytes.decode()


def check_openid_signature(openid_sign):
    """对openid进行解密,并返回原生openid"""

    # 创建加密对象
    serializer = Serializer(settings.SECRET_KEY, 600)
    try:
        # 调用它里面的loads方法进行解密
        data = serializer.loads(openid_sign)
    except BadData:
        return None
    else:
        # 获取解密后字典中的openid并返回
        return data.get('openid')