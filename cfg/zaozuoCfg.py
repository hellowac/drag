# coding:utf-8

from . import InstanceCfg


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'ZAOZUO'

    #修改父类变量在init方法中修改
    def __init__(self):
        self.MAX_RETRIES = 15
        self.DEFAULT_SIZE_SKU = '001'
        self.DEFAULT_COLOR_SKU = '001'
        self.DEFAULT_ONE_SIZE = 'One Size'
        self.DEFAULT_ONE_COLOR = 'One Color'
