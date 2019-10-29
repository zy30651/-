import logging
import re
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from celery_tasks.email.tasks import send_verify_email
from .utils import get_user_by_account
from .models import User

logger = logging.getLogger('django')


class CreateUserSerializers(serializers.ModelSerializer):
    """创建用户序列化器"""
    password2 = serializers.CharField(label='确认密码', required=True, allow_null=False, allow_blank=False, write_only=True)
    sms_code = serializers.CharField(label='短信验证码', required=True, allow_null=False, allow_blank=False, write_only=True)
    allow = serializers.CharField(label='同意协议', required=True, allow_null=False, allow_blank=False, write_only=True)
    token = serializers.CharField(label='登录状态token', read_only=True)

    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[345789]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def validate_allow(self, value):
        """检验用户是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, data):
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断短信验证码
        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_data):
        """
        创建用户
        """
        # 移除数据库模型类中不存在的属性
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        user = super().create(validated_data)

        # 调用django的认证系统加密密码
        user.set_password(validated_data['password'])
        user.save()

        # 手动为用户生成JWT token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        # 将token保存到user对象中，随着返回值返回给前端
        user.token = token

        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', 'token')
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }


class CheckSMSCodeSerializer(serializers.Serializer):
    """
    检查SMS code
    """
    sms_code = serializers.CharField(min_length=6, max_length=6)

    def validate_sms_code(self, value):
        account = self.context['view'].kwargs['account']
        user = get_user_by_account(account)

        if user is None:
            raise serializers.ValidationError('用户不存在')

        # 把User对象保存到序列化对象当中
        self.user = user

        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % user.mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if value != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')
        return value


class ResetPasswordSerializer(serializers.ModelSerializer):
    """
    重置密码序列化器
    """
    password2 = serializers.CharField(label='确认密码', write_only=True)
    access_token = serializers.CharField(label='操作Token', write_only=True)

    class Meta:
        model = User
        fields = ('id', 'password', 'password2', 'access_token')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate(self, attrs):
        """校验数据"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断access token
        # 需要对比 access_token的user_Id,和请求用户的id是否一致
        allow = User.check_set_password_token(attrs['access_token'], self.context['view'].kwargs['pk'])
        if not allow:
            raise serializers.ValidationError('无效的access token')

        return attrs

    def update(self, instance, validated_data):
        """
        更新密码
        """
        # 调用django 用户模型类的设置密码方法
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户详细信息序列化器
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email')
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        """重写更新方法，添加发送邮件"""
        email = validated_data['email']
        instance.email = email
        instance.save()

        # 生成激活链接
        verify_url = instance.generate_email_verify_url()
        # 发送验证邮件
        send_verify_email.delay(email, verify_url)
        return instance

