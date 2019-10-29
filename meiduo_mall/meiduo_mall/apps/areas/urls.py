from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from . import views

route = DefaultRouter()
route.register('areas', views.AreasViewSet, base_name='area')

urlpatterns = [
    # url('', include(route.urls))
]

urlpatterns += route.urls
