from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from . import constants
from rest_framework.generics import GenericAPIView
from . import serializers
import random
from meiduo_mall.libs.AliSMS.sms import CCP, SMS_SignName, SMS_Template_Code
from rest_framework.response import Response


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
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 校验通过
        # 1:生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        # 2：保存验证码，及发送记录
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        redis_conn.setex('send_flag_%s' % mobile, constants.SendSMS_CODE_REDIS_EXPIRES, 1)
        # 3：发送
        ccp = CCP()
        ccp.send_template_sms(mobile, SMS_SignName, SMS_Template_Code, {'code': sms_code})
        # 4：返回
        return Response({'message': 'OK'})
