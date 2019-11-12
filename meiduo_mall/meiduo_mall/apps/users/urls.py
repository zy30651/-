from django.conf.urls import url
from . import views
# from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import DefaultRouter

urlpatterns = [
    url(r'^users/$', views.UserView.as_view()),
    url(r'usernames/(?P<username>\w{5,20})/count/', views.UsernameCountView.as_view()),
    url(r'mobiles/(?P<mobile>1[345789]\d{9})/count/', views.MobileCountView.as_view()),
    # url(r'^authorizations/$', obtain_jwt_token),
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),
    url(r'^accounts/(?P<account>\w{4,20})/sms/token/$', views.SMSCodeToken.as_view()),   # 获取发送短信验证码
    url(r'^accounts/(?P<account>\w{4,20})/password/token/$', views.PasswordTokenView.as_view()),   # 获取发送短信验证码
    url(r'users/(?P<pk>\d+)/password/$', views.PasswordView.as_view()),     # 重置密码
    url(r'^user/$', views.UserDetailView.as_view()),     # 用户个人中心数据
    url(r'^emails/$', views.EmailView.as_view()),     # 保存邮箱并发送验证邮件
    url(r'^emails/verification/$', views.EmailVerifyView.as_view()),
    url(r'browse_histories/$', views.UserHistoryView.as_view())
]

router = DefaultRouter()
router.register('addresses', views.AddressViewSet, base_name='addresses')

urlpatterns += router.urls
