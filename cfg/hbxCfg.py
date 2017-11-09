# coding:utf-8

from . import InstanceCfg
from requests.cookies import RequestsCookieJar


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'HBX'

    #修改父类变量在init方法中修改
    def __init__(self):
        self.USE_COOKIES = True

        cookieJar = RequestsCookieJar()

        #设置地区
        cookieJar.set('hbx_catalog_country','HK')

        self.COOKIEJAR = cookieJar
