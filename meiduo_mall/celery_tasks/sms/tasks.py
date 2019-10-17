from .AliSMS.sms import CCP, SMS_SignName, SMS_Template_Code
from celery_tasks.main import celery_app


@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    """
    发送短信任务
    :param mobile:手机号
    :param sms_code: 验证码
    :return:None
    """

    ccp = CCP()
    ccp.send_template_sms(mobile, SMS_SignName, SMS_Template_Code, {'code': sms_code})

    pass
