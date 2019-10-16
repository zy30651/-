from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

# 短信参数名
import json

ALi_RegionId = 'RegionId'
ALi_SignName = 'SignName'
ALi_PhoneNumbers = 'PhoneNumbers'
ALi_TemplateCode = 'TemplateCode'
ALi_TemplateParam = 'TemplateParam'

# SMS-Access Key Secret
SMS_AccessKeySecret = 'CaOB4i8DeE9E7Sc2Kn3CanbciEVx4B'
# SMS-AccessKey ID
SMS_AccessKeyID = 'LTAI0x0FXrd6G3ht'
SMS_RegionId = 'cn-hangzhou'
# SMS-签名名称
SMS_SignName = '毅杰国际'
# SMS_模板code
SMS_Template_Code = 'SMS_172365002'
# SMS_模板SMS_172365002的参数-code


class CCP(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(CCP, "_instance"):
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            cls._instance.client = AcsClient(SMS_AccessKeyID, SMS_AccessKeySecret, SMS_RegionId)
            cls._instance.request = CommonRequest()
            cls._instance.request.set_accept_format('json')
            cls._instance.request.set_domain('dysmsapi.aliyuncs.com')
            cls._instance.request.set_method('POST')
            cls._instance.request.set_protocol_type('https')  # https | http
            cls._instance.request.set_version('2017-05-25')
            cls._instance.request.set_action_name('SendSms')
        return cls._instance

    def send_template_sms(self, number, sign_name, temp_code, temp_param):
        self.request.add_query_param(ALi_RegionId, SMS_RegionId)
        self.request.add_query_param(ALi_PhoneNumbers, number)
        self.request.add_query_param(ALi_SignName, sign_name)
        self.request.add_query_param(ALi_TemplateCode, temp_code)
        self.request.add_query_param(ALi_TemplateParam, temp_param)
        response = self.client.do_action_with_exception(self.request)
        response = json.loads(response)
        if response.get('Message') == 'OK':
            return 0
        else:
            return -1


if __name__ == '__main__':
    ccp = CCP()
