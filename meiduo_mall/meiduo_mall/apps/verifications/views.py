from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from . import constants
from rest_framework.generics import GenericAPIView
from . import serializers


class ImageCodeView(APIView):
    """
    图片验证码
    """
    def get(self, request, image_code_id):
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        return HttpResponse(image, content_type="images/jpg")


class SMSCodeView(GenericAPIView):
    serializer_class = serializers.CheckImageCodeSerializer

    def get(self, request, mobile):
        # 校验图片码和发送短信的频次
        # mobile 是放到了类视图中,叫kwargs中
        serializer = self.get_serializer()
        serializer.is_valid(raise_exception=True)

