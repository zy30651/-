# 公共方法
from django.contrib.auth.backends import ModelBackend
import re

from .models import User


def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    :param token:
    :param user:
    :param request:
    :return:
    """
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


def get_user_by_account(account):
    """
    根据账号信息查找用户对象
    :param account: 可以是手机号，也可以是用户名
    :return:
    """
    # 判断是否是手机号
    # 是，根据手机号查询
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            # 根据手机号查询
            user = User.objects.get(mobile=account)
        # 不是，根据username查询
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    return user


class UsernameMobileAuthBackend(ModelBackend):
    """
    自定义认证方法客户端
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 根据username查询用户对象:username可能是用户名或者手机号
        user = get_user_by_account(username)
        # 如果用户对象存在，调用check_password方法验证密码
        if user is not None and user.check_password(password):
            # 验证成功，返回user对象
            return user
