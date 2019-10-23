from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer
from django.conf import settings
# Create your models here.
from users.constants import SEND_SMS_CODE_TOKEN_EXPIRES


class User(AbstractUser):
    """用户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")

    class Meta:
        db_table = "tb_users"
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def generate_send_sms_code_token(self):
        """
        生成发送短信验证码的access_token
        :return: token
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, SEND_SMS_CODE_TOKEN_EXPIRES)
        data = {
            'mobile': self.mobile
        }
        token = serializer.dumps(data)
        return token.decode()

