from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import OrderInfo
from alipay import AliPay
from django.conf import settings
import os


class PaymentView(APIView):
    """支付宝支付"""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        user = request.user
        # 校验订单order_id
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return Response({'message': '订单信息有误'}, status=status.HTTP_404_NOT_FOUND)

        # 根据订单的数据，向支付宝发起请求，获取支付连接的参数
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url="http://www.cocsite.cn:8080/pay_success.html",
        )

        # 拼接连接返回前端
        alipay_url = settings.ALIPAY_URL + "?" + order_string

        return Response({'alipay_url': alipay_url}, status=status.HTTP_201_CREATED)
