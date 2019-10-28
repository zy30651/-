from django.conf import settings
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen
import logging
import json

from .exceptions import QQAPIException

logger = logging.getLogger('django')


class OAuthQQ(object):
    """
    用户QQ登陆工具类
    提供QQ登陆可能用的方法
    """
    def __init__(self, app_id=None, app_key=None, redirect_uri=None, state=None):
        self.app_id = app_id or settings.QQ_APP_ID
        self.app_key = app_key or settings.QQ_APP_KEY
        self.redirect_uri = redirect_uri or settings.QQ_APP_REDIRECT_URI
        self.state = state or settings.QQ_STATE

    def generate_qq_login_url(self):
        """
        拼接用户QQ登陆的链接地址
        :return:
        """
        url = 'https://graph.qq.com/oauth2.0/authorize?'
        data = {
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope': 'get_user_info'     # 获取用户的openid
        }
        query_string = urlencode(data)   # response_type=code&client_id=xxx&redirect_url=xxxx&...
        url += query_string
        return url

    def get_access_token(self, code):
        """
        获取QQ-access_token
        :param code: 调用的凭证
        :return: access_token
        """
        url = 'https://graph.qq.com/oauth2.0/token?'
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.app_id,
            'client_secret': self.app_key,
            'redirect_uri': self.redirect_uri,
            'code': code
        }
        url += urlencode(data)

        try:
            # 发送请求
            response = urlopen(url)
            # 读取响应数据
            response = response.read().decode()
            # 将返回的数据转换为字典
            resp_dict = parse_qs(response)

            access_token = resp_dict.get('access_token')[0]
        except Exception as e:
            logging.error(e)
            raise QQAPIException('获取access_token异常')

        return access_token

    def get_openid(self, access_token):
        """
        获取用户的openid
        :param access_token: qq提供的access_token
        :return: open_id
        """
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token

        try:
            # 发送请求
            response = urlopen(url)
            # 读取响应数据
            response_data = response.read().decode()
            # 将字符串切片 callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} )\n;
            data = json.loads(response_data[10:-4])
        except Exception:
            data = parse_qs(response_data)
            logging.error('code=%s msg=%s' % (data.get('code'), data.get('msg')))
            raise QQAPIException('获取openid异常')

        openid = data.get('openid', None)
        return openid


