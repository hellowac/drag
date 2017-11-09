# coding:utf-8

from . import InstanceCfg
from requests.cookies import RequestsCookieJar


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'EASTDANE'

    #修改父类变量在init方法中修改
    def __init__(self):
        cookieJar = RequestsCookieJar()
        cookieJar.set('lc-main','en_US')
        self.COOKIEJAR = cookieJar
        pass