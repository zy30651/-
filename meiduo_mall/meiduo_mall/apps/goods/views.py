from django.shortcuts import render
from rest_framework.generics import ListAPIView
from .serializers import SKUSerializer
# Create your views here.


class HotSKUListView(ListAPIView):
    """返回热销数据"""
    queryset =
    serializer_class = SKUSerializer
    pass
