from django.conf import settings
from urllib.parse import urlencode


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
        print(url)
        return url

