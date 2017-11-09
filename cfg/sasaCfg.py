# coding:utf-8

from . import InstanceCfg
from requests.cookies import RequestsCookieJar


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'SASA'

    #修改父类变量在init方法中修改
    def __init__(self):
        self.USE_COOKIES = True

        cookieJar = RequestsCookieJar()

        
        cookieJar.set('location','0')	#地区，香港；(0,香港),(3,大陆),
        cookieJar.set('currency','1')	#设置货币,港元,(1，本地货币)
        cookieJar.set('currencyId','HKD')	#设置货币,港元,(1，本地货币)

        cookieJar.set('countryCode','HK')	#设置地区，香港

        cookieJar.set('language','23')	#设置语言,简体中文,(23，繁体中文)
        cookieJar.set('languageId','zh_CN')	#设置语言,简体中文
        

        self.COOKIEJAR = cookieJar
