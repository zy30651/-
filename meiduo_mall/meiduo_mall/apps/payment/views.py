from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import OrderInfo, Payment
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
            appid=settings.ALIPAY_DEV_APPID,
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
        alipay_url = settings.ALIPAY_DEV_URL + "?" + order_string

        return Response({'alipay_url': alipay_url}, status=status.HTTP_201_CREATED)
# 7576    7530.54
# 99999   92423.00
class PaymentStatusView(APIView):
    """
    支付结果
    """
    def put(self, request):
        # 取出请求的参数
        data = request.query_params.dict()

        # 校验请求的参数是否是支付宝的参数
        # 是，验证成功，保存支付数据，修改订单数据
        # 返回
        # data = request.dict() # django ,但是在rest里边需要使用query_params

        signature = data.pop("sign")

        alipay_client = AliPay(
            appid=settings.ALIPAY_DEV_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )
        # verification
        success = alipay_client.verify(data, signature)
        if success:
            # 保存支付数据
            # 订单编号
            order_id = data.get('out_trade_no')
            # 支付宝支付流水号
            trade_id = data.get('trade_no')
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])\
                .update(status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])
            return Response({'trade_id': trade_id})
            # 修改订单数据

        else:
            # 如果参数不是支付宝，则是非法请求
            return Response({'message': '非法请求'}, status=status.HTTP_403_FORBIDDEN)
