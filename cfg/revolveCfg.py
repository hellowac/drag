#coding:utf-8

from . import InstanceCfg
from requests.cookies import RequestsCookieJar

class Cfg(InstanceCfg):
    # asos 渠道 自定义配置

    CFG_NAME = 'REVOLVE'

    #修改父类变量在init方法中修改
    def __init__(self):
        self.USE_COOKIES = True

        #是否启用代理
        self.USE['PROXY'] = True

        #代理类型
        self.USE['PROXY_TYPE'] = 'GENERAL'     #另外一种 SOCKS
        # self.USE['PROXY_TYPE'] = 'SOCKS'     #另外一种 SOCKS

        cookieJar = RequestsCookieJar()

        #设置语言
        cookieJar.set('userLanguagePref','en')

        #设置货币符号,但是设置了没用!2016-08-15 16:03:11
        cookieJar.set('currency','USD')
        cookieJar.set('currencyOverride','usd')
        # cookieJar.set('userLanguagePref','zh')


        self.COOKIEJAR = cookieJar