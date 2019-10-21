from django.http import HttpResponse
from rest_framework.views import APIView
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from . import constants
from rest_framework.generics import GenericAPIView
from . import serializers
import random
from rest_framework.response import Response
from celery_tasks.sms.tasks import send_sms_code


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
        # 2：保存验证码，及发送记录 使用redis的pipeline管道，可以一次执行多个命令
        redis_conn = get_redis_connection('verify_codes')

        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SendSMS_CODE_REDIS_EXPIRES, 1)
        # 让管道执行命令
        pl.execute()

        # 3：发送 使用celery发布异步任务
        send_sms_code.delay(mobile, sms_code)

        # 4：返回
        return Response({'message': 'OK'})
