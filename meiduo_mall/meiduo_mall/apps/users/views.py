from rest_framework import mixins
from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import re
from . import serializers
from .models import User
from verifications.serializers import CheckImageCodeSerializer
from .utils import get_user_by_account
from rest_framework.permissions import IsAuthenticated

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


class PasswordView(GenericAPIView, mixins.UpdateModelMixin):
    """
    用户密码
    """
    queryset = User.objects.all()
    serializer_class = serializers.ResetPasswordSerializer

    def post(self, request, pk):
        return self.update(request, pk)


class UserDetailView(RetrieveAPIView):
    """
    用户详情信息
    /users/<pk>/
    /user/
    """
    serializer_class = serializers.UserDetailSerializer
    # 补充通过认证后才能访问接口的权限
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        返回请求用户对象
        类视图对象中也保存了请求对象request
        request对象的user属性是通过认证插眼后的请求用户对象
        类视图对象还有kwargs属性
        :return: user
        """
        return self.request.user


class EmailView(UpdateAPIView):
    """
    保存邮箱
    /email/
    """
    serializer_class = serializers.EmailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    # 第二种实现方式
    # def get_serializer(self, *args, **kwargs):
    #     return EmailSerialier(self.request.user, data=self.request.data)




