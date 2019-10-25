from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import re
from . import serializers
from .models import User
from verifications.serializers import CheckImageCodeSerializer
from .utils import get_user_by_account

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


class UserView(CreateAPIView):
    """
    用户注册
    """
    serializer_class = serializers.CreateUserSerializers


class SMSCodeToken(GenericAPIView):
    """
    获取发送短信验证码凭据
    """
    serializer_class = CheckImageCodeSerializer

    def get(self, request, account):
        """
        校验图片验证码是否正确
        :param request:
        :par am account:
        :return:
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 根据account账号查询user对象
        user = get_user_by_account(account)
        if user is None:
            return Response({"message": '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 根据user对象的手机号生成access_token
        access_token = user.generate_send_sms_code_token()

        # 修改手机号
        mobile = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', user.mobile)

        return Response({
            'mobile': mobile,
            'access_token': access_token
        })


class PasswordTokenView(GenericAPIView):
    """
    用户账户设置密码的token
    """
    serializer_class = serializers.CheckSMSCodeSerializer

    def get(self, request, account):
        """
        根据用户账户获取修改密码的token
        :param request:
        :param account:
        :return:
        """
        # 校验access Token
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        # 生成修改用户密码的access token
        access_token = user.generate_set_password_token()

        return Response({'user_id': user.id, 'access_token': access_token})
