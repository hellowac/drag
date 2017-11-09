# coding:utf-8

from . import InstanceCfg


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'MVMTWATCHES'

    #修改父类变量在init方法中修改
    def __init__(self):
        self.DEFAULT_ONE_COLOR = 'One Color'
        self.DEFAULT_STOCK_NUMBER = 50
