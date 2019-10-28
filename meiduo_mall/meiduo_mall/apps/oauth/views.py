from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import OAuthQQ

# Create your views here.


class OAuthQQURLView(APIView):
    """
    提供QQ登陆的网址
    前端请求的网址：/oauth/qq/authorization/?state=xxxxx
    state参数有前端传递，参数值为qq登陆成功后，后端引导到那个页面
    """
    def get(self, request):
        # 提取state参数
        state = request.query_params.get('state')
        if not state:
            state = '/'     # 如果前端未指明，默认登陆成功后跳转到主页

        # 按照qq说明文档，拼接用户qq登陆的链接地址
        oauth_qq = OAuthQQ()
        login_url = oauth_qq.generate_qq_login_url()
        # 返回链接地址
        return Response({'oauth_url': login_url})
