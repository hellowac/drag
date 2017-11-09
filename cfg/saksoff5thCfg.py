#coding:utf-8

from . import InstanceCfg

class Cfg(InstanceCfg):
    # asos 渠道 自定义配置

    CFG_NAME = 'SAKSOFF5TH'

    #修改父类变量在init方法中修改
    def __init__(self):
        
        
        # #是否启用代理
        self.USE['PROXY'] = True 

        # #代理类型，https
        self.USE['PROXY_TYPE'] = 'GENERAL'