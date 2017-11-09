# coding:utf-8

from . import InstanceCfg
from requests.cookies import RequestsCookieJar


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'MACYS'

    #修改父类变量在init方法中修改
    def __init__(self):
        self.USE_COOKIES = True

        cookieJar = RequestsCookieJar()

        cookieJar.set('shippingCountry','US')
        cookieJar.set('currency','USD')
        # cookieJar.set('shippingCountry','HK')
        # cookieJar.set('currency','HKD')

        self.COOKIEJAR = cookieJar
