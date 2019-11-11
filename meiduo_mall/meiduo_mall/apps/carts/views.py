import base64
import pickle

from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
# Create your views here.
from .serializers import CartSerializer, CartSKUSerializer
from goods.models import SKU


class CartView(APIView):
    """购物车视图"""
    def perform_authentication(self, request):
        """重写检查jwt token是否正确"""
        pass

    def get(self, request):
        """查询购物车逻辑"""
        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            # 前端携带了错误JWT token，用户未登录
            user = None

        if user is not None and user.is_authenticated:
            # 如果用户登录，从redis查询
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
            # 将 redis 读取的数据，进行整合，形成一个字典，与cookie解读的数据一致，方便查询
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }
        else:
            # 如果用户未登录，从cookie查询
            cart_str = request.COOKIES.get('cart')

            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

        # 数据库查询sku对象
        sku_id_list = cart_dict.keys()
        sku_obj_list = SKU.objects.filter(id__in=sku_id_list)
        # 查询的结果，并没有count, selected
        # 补充数据
        for sku in sku_obj_list:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        serializer = CartSKUSerializer(sku_obj_list, many=True)
        return Response(serializer.data)

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

    def put(self, request):
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

        if user is not None and user.is_authenticated:
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hset('cart_%s' % user.id, sku_id, count)
            if selected:
                # 勾选添加记录
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                # 删除记录
                pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            return Response(serializer.data)
        else:
            cart_str = request.COOKIES.get('cart')
            # 需要base64解码，但是base64解码只接受字节类型，所以需要先encode,然后结果还是字节类型
            # 再pickle解析
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

            if sku_id in cart_dict:
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            cookie_cart = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response = Response(serializer.data)    # 不设置状态码，默认200
            response.set_cookie('cart', cookie_cart)
            return response

    # def delete(self):
    #     pass
