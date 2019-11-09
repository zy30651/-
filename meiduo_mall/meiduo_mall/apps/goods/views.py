from django.shortcuts import render
from rest_framework.generics import ListAPIView
from . import constants
from .serializers import SKUSerializer, SKUIndexSerializer
from .models import SKU
from rest_framework_extensions.cache.mixins import ListCacheResponseMixin
# Create your views here.
from rest_framework.filters import OrderingFilter
from drf_haystack.viewsets import HaystackViewSet


class HotSKUListView(ListCacheResponseMixin, ListAPIView):
    """返回热销数据"""
    serializer_class = SKUSerializer
    pagination_class = None

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return SKU.objects.filter(category_id=category_id,
                                  is_launched=True).order_by('-sales')[:constants.HOT_SKUS_COUNT_LIMIT]


class SKUListView(ListAPIView):
    """
    sku列表数据
    """
    serializer_class = SKUSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ('create_time', 'price', 'sales')

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return SKU.objects.filter(category_id=category_id, is_launched=True)


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    serializer_class = SKUIndexSerializer
