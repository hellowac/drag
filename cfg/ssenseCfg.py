# coding:utf-8

from . import InstanceCfg
from requests.cookies import RequestsCookieJar


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'SSENSE'

    #修改父类变量在init方法中修改
    def __init__(self):
        cookieJar = RequestsCookieJar()

        #地区
        cookieJar.set('continent','NA')
        cookieJar.set('country','US')
        cookieJar.set('currency','USD')
        cookieJar.set('forcedCountry','US')
        cookieJar.set('lang','en_US')

        self.COOKIEJAR = cookieJar

        # self.USE['PROXY'] = True 

        # self.USE['PROXY_TYPE'] = 'GENERAL'     #另外一种 SOCKS
        # self.USE['PROXY_TYPE'] = 'SOCKS'     #另外一种 SOCKS
