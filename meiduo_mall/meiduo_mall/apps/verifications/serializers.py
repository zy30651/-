from rest_framework import serializers
from django_redis import get_redis_connection
from redis.exceptions import RedisError
import logging

logger = logging.getLogger('django')


class CheckImageCodeSerializer(serializers.Serializer):
    """
    图片验证码校验序列化器
    """
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):
        """
        校验图片验证码,需要多参数同时校验
        校验的问题：
        """
        # 查询redis数据库获取验证码
        text = attrs["text"]
        image_code_id = attrs['image_code_id']
        redis_conn = get_redis_connection('verify_codes')
        real_image_code = redis_conn.get('img_%s' % image_code_id)
        # 对比
        if real_image_code is None:
            # 过期或不存在
            raise serializers.ValidationError('无效图片验证码')

        # 删除redis中的图片验证码，防止用户对一个进行多次验证；因为不希望有特殊处理，所以pass
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            logger.error(e)

        # 转换
        real_image_code = real_image_code.decode()
        if real_image_code.lower() != text.lower():
            raise serializers.ValidationError('图片验证码错误')

        # redis 中发送短信验证码的标志：send_flag_<mobile> : 1 60秒发送过短信，
        mobile = self.context['view'].kwargs['mobile']
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            raise serializers.ValidationError('发送短信次数过于频繁')

        return attrs
