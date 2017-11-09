# coding:utf-8

from . import InstanceCfg
from requests.cookies import RequestsCookieJar


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'MATCHESFASHION'

    #修改父类变量在init方法中修改
    def __init__(self):
        self.USE_COOKIES = True
        
    	cookieJar = RequestsCookieJar()

        # cookieJar.set('country','CHN')
        cookieJar.set('country','HKG',domain='www.matchesfashion.com',path='/')
        cookieJar.set('gender','mens',domain='www.matchesfashion.com',path='/')
        cookieJar.set('language','en',domain='www.matchesfashion.com',path='/')
        # cookieJar.set('loggedIn','false',domain='www.matchesfashion.com',path='/')
        cookieJar.set('billingCurrency','HKD',domain='www.matchesfashion.com',path='/')
        cookieJar.set('indicativeCurrency','CNY',domain='www.matchesfashion.com',path='/')

        self.COOKIEJAR = cookieJar
