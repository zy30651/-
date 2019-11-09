from rest_framework import serializers
from .models import SKU
from drf_haystack.serializers import HaystackSerializer
from .search_indexes import SKUIndex


class SKUSerializer(serializers.ModelSerializer):
    """SKU序列化器"""
    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')


# 构建索引化序列化器
class SKUIndexSerializer(HaystackSerializer):
    """
    haystack使用的序列化器
    """
    class Meta:
        index_classes = [SKUIndex]
        fields = ('text', 'id', 'name', 'price', 'default_image_url', 'comments')
