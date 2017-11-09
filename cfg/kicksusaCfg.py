# coding:utf-8

from . import InstanceCfg


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'KICKSUSA'

    #修改父类变量在init方法中修改
    def __init__(self):
        # self.USE['PROXY'] = True
        # self.USE['PROXY_TYPE'] = 'SOCKS'
        self.USE['PROXY_TYPE'] = 'GENERAL'