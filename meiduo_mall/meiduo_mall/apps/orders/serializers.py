from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, APIException
from goods.models import SKU
from .models import OrderInfo, OrderGoods
from django.db import transaction
from django.utils import timezone
from decimal import Decimal


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True, read_only=True)


class SaveOrderSerializer(serializers.ModelSerializer):
    """保存订单的序列化器"""
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')

        # 'write_only': 向后端写数据，向后端传数据
        # 'read_only': 前端要从后端读取数据，后端返回数据使用
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        """保存订单"""
        # 获取当前下单用户
        user = self.context['request'].user     # 序列化操纵request，需要使用self.context
        # 保存订单的基本信息数据 OrderInfo 组织订单信息 20170903153611+user.id
        # time.time是时间戳，从1970年开始的秒数
        # time.datetime
        # django.utils import timezone  返回当前的时区的时间
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%9d' % user.id)

        with transaction.atomic():
            # 创建一个保存点
            save_id = transaction.savepoint()

            try:
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=validated_data['address'],
                    total_count=0,
                    total_amount=Decimal(0),
                    freight=Decimal(10),
                    pay_method=validated_data['pay_method'],
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                    if validated_data['pay_method'] == OrderInfo.PAY_METHODS_ENUM['CASH']
                    else OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )

                # 获取购物车信息
                redis_conn = get_redis_connection("cart")
                redis_cart = redis_conn.hgetall('cart_%s' % user.id)
                cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

                cart = {}

                for sku_id in cart_selected:
                    cart[int(sku_id)] = int(redis_cart[sku_id])

                total_amount = Decimal('0')
                total_count = 0

                skus = SKU.objects.filter(id__in=cart.keys())

                for sku in skus:
                    # 判断商品库存是否充足
                    sku_count = cart[sku.id]

                    if sku.stock < sku_count:
                        # 事务回滚
                        transaction.savepoint_rollback(save_id)
                        raise serializers.ValidationError({'detail': '商品库存不足'})

                    sku.stock -= sku_count
                    sku.sales -= sku_count

                    sku.save()

                    total_amount += sku.price * sku_count
                    total_count += sku_count

                    # 保存到OrderGoods
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=sku_count,
                        price=sku.price,
                    )

                # 更新订单的金额数量信息
                order.total_amount = total_amount
                order.total_amount += order.freight
                order.total_count = total_count
                order.save()

            except ValidationError:
                raise
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                raise APIException('保存订单失败')

            # 提交事务
            transaction.savepoint_commit(save_id)

            # 清除redis中购物车应结算的商品
            # for sku_id in cart_selected:
            #     del redis_cart[sku_id]

            pl = redis_conn.pipeline()

            # pl.hmset('cart_%s' % user.id, redis_cart)
            pl.hdel('cart_%s' % user.id, *cart_selected)
            pl.srem('cart_selected_%s' % user.id, *cart_selected)
            pl.execute()

            return order



