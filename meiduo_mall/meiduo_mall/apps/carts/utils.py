import base64
import pickle

from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, response, user):
    """
    合并购物车, cookie保存到redis
    :return:
    """
    # 从cookie中取出购物车数据
    cart_str = request.COOKIES.get('cart')

    if not cart_str:
        return response

    cookie_cart = pickle.loads(base64.b64decode(cart_str.encode()))

    # 从redis中取出购物车数据
    redis_conn = get_redis_connection('cart')
    cart_redis = redis_conn.hgetall('cart_%s' % user.id)
    # 将redis取出的字典的键值对数据类型(字节类型)改为 int类型

    cart = {}
    for sku_id, count in cart_redis.items():
        cart[int(sku_id)] = int(count)

    # 将cookie的数据合并到redis中
    selected_sku_id_list = []
    for sku_id, selected_count_dict in cookie_cart.items():
        cart[sku_id] = selected_count_dict['count']

        # 处理勾选状态, 如果当前
        if selected_count_dict['selected']:
            selected_sku_id_list.append(sku_id)

    pl = redis_conn.pipeline()
    pl.hmset('cart_%s' % user.id, cart)

    pl.sadd('cart_selected_%s' % user.id, *selected_sku_id_list)
    pl.execute()

    # 清空cookie的购物车数据
    response.delete_cookie('cart')

    return response
