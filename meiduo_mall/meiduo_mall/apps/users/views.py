from rest_framework.response import Response
from rest_framework.views import APIView
from meiduo_mall.apps.users.models import User
# Create your views here.


class UsernameCountView(APIView):
    """
    获取指定用户名数量
    """
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        data = {
            'username': username,
            'count': count
        }
        return Response(data)


class MobileCountView(APIView):
    """
    获取指定手机号数量
    """
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        data = {
            'mobile': mobile,
            'count': count
        }
        return Response(data)
