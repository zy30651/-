import base64
import pickle

from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
# Create your views here.
from .serializers import CartSerializer


class CartView(APIView):
    """购物车视图"""
    def perform_authentication(self, request):
        """重写检查jwt token是否正确"""
        pass

    def get(self):
        pass

    def post(self, request):
        """保存购物车数据"""
        # 检查前端发送数据是否正确 1可以此处检查或者放入序列化器
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            # 前端携带了错误JWT token，用户未登录
            user = None

        # 保存购物车数据
        if user is not None and user.is_authenticated:
            # 用户已登录保存如redis
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()

            # 购物车数据hash
            pl.hincrby('cart_%s' % user.id, sku_id, count)

            # 判断是否勾选
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)

            pl.execute()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # 用户未登录保存如cookie
            # 尝试从cookie中读取购物车数据
            cart_str = request.COOKIES.get('cart')
            # 需要base64解码，但是base64解码只接受字节类型，所以需要先encode,然后结果还是字节类型
            # 再pickle解析
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}
            # 如果有相同商品，求和
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cookie_cart = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            response.set_cookie('cart', cookie_cart)
            return response

    # def put(self):
    #     pass
    #
    # def delete(self):
    #     pass
