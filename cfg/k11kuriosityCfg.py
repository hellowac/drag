# coding:utf-8

from . import InstanceCfg


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'K11KURIOSITY'

    # 覆盖掉类属性.
    def __init__(self):
        self.DEFAULT_ONE_COLOR = 'One Color'
