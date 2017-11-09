# coding:utf-8

from . import InstanceCfg
from requests.cookies import RequestsCookieJar


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'TOPMAN'

    #修改父类变量在init方法中修改
    def __init__(self):

        self.USE_COOKIES = True

        cookieJar = RequestsCookieJar()

        cookieJar.set('s_cc', 'true')
        cookieJar.set('usergeo','CN')
        cookieJar.set('geoIpCtry','CN')
        cookieJar.set('s_invisit','true')
        cookieJar.set('prefShipCtry', 'GB')
        cookieJar.set('__qubitCountryAU','CN')
        cookieJar.set('__qubitCountryUK','CN')
        cookieJar.set('REFERRER', 'http%3A%2F%2Fwww.topman.com%2F')

        self.COOKIEJAR = cookieJar

        #是否启用代理
        # self.USE['PROXY'] = True 

        #代理类型
        # self.USE['PROXY_TYPE'] = 'GENERAL'     #另外一种 SOCKS
        # InstanceCfg.USE['PROXY_TYPE'] = 'SOCKS'     #另外一种 SOCKS

        pass
