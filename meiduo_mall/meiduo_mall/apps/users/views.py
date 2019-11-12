from django_redis import get_redis_connection
from rest_framework import mixins
from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
import re

from carts.utils import merge_cart_cookie_to_redis
from goods.models import SKU
from goods.serializers import SKUSerializer
from . import serializers, constants
from .models import User
from verifications.serializers import CheckImageCodeSerializer
from .utils import get_user_by_account
from rest_framework.permissions import IsAuthenticated
from rest_framework_jwt.views import ObtainJSONWebToken
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


class EmailVerifyView(APIView):
    """邮箱验证"""
    def get(self, request):
        # 获取token
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # 使用序列化器校验
        result = User.check_email_verify_token(token)
        # 保存
        if result:
            return Response({'message': 'OK'})
        else:
            return Response({'message': '链接信息无效'}, status=status.HTTP_400_BAD_REQUEST)


class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = serializers.UserAddressSerializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# 如果操作序列化器，需要使用GenericAPIView， APIView不支持序列化器
class UserHistoryView(mixins.CreateModelMixin, GenericAPIView):
    """用户的历史记录"""
    permission_classes = [IsAuthenticated]  # 加了权限控制，序列化器就能拿到token
    serializer_class = serializers.AddUserHistorySerializer

    def post(self, request):
        """保存"""
        return self.create(request)

    # serializer_class =
    def get(self, request):
        # 查询redis数据库
        user_id = request.user.id
        redis_conn = get_redis_connection('history')
        sku_id_list = redis_conn.lrange('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT-1)

        # 根据redis返回的sku_id查询数据库
        # SKU.objects.filter(id__in=sku_id_list) # 使用__in可以查，但是查询后数据库会被打乱,会按照数据库的顺序查询出来
        sku_list = []
        for sku_id in sku_id_list:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append(sku)

        # 使用序列化器序列化
        s = SKUSerializer(sku_list, many=True)
        return Response(s.data)


class UserAuthorizeView(ObtainJSONWebToken):
    """
    用户认证
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user') or request.user
            response = merge_cart_cookie_to_redis(request, user, response)

        return response







