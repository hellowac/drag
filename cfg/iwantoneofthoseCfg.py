# coding:utf-8

from . import InstanceCfg


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'IWNATONEOFTHOSE'

    EVERLANE_ONE_COLOR = True	#False/True 获取多颜色,否则只获取单颜色

    #修改父类变量在init方法中修改
    def __init__(self):
        pass