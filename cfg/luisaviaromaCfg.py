# coding:utf-8

from . import InstanceCfg
from requests.cookies import RequestsCookieJar


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'LUISAVIAROMA'

    #修改父类变量在init方法中修改
    def __init__(self):
        self.USE_COOKIES = True

        cookieJar = RequestsCookieJar()

        #设置城市(cty),结算货币(curr),显示货币(vcurr),语言(lang)
        cookieJar.set('LVR_UserData','cty=HK&curr=EUR&vcurr=HKD&flgcurr=1&lang=EN&Ver=4')

        #设置其他货币符号,
        # cookieJar.set('LVR_UserData','cty=HK&curr=EUR&vcurr=HKD&flgcurr=1&lang=EN&Ver=4')

        self.COOKIEJAR = cookieJar
