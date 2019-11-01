from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from fdfs_client.client import Fdfs_client

from django.conf import settings


@deconstructible
class FastDFSStorage(Storage):
    """自定义文件存储系统"""
    def __init__(self, client_conf=None, base_url=None):
        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

        if client_conf:
            self.client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

    # def _open(self, name, mode='rb'):
    #     """目前只用来保存，暂不需要打开，所以省略"""
        pass

    def _save(self, name, content):
        """
        保存文件
        :param name:前端传递文件名
        :param content:文件数据
        :return:存储到数据库的文件信息
        """
        # 保存到FastDFS里边
        client = Fdfs_client(self.client_conf)
        ret = client.upload_by_buffer(content.read())

        if ret.get('status') != 'Upload successed.':
            raise Exception('Upload file failed')
        file_name = ret.get('Remote file_id')
        return file_name

    def url(self, name):
        """
        返回文件的完整URL路径
        :param name: 数据库中保存的文件名
        :return: 完整的URL
        """
        return self.base_url + name

    def exists(self, name):
        """
        判断文件是否存在，FastDFS可以自行解决文件的重名问题
        所以此处返回False，告诉Django上传的都是新文件
        :param name:  文件名
        :return: False
        """
        return False
