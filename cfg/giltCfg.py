# coding:utf-8

from . import InstanceCfg


class Cfg(InstanceCfg):
    # 渠道 自定义配置

    CFG_NAME = 'GILT'

    # 修改父类变量在init方法中修改
    def __init__(self):
        # gilt 开发商品请求接口.
        self.api_key = 'd1d58190910c07ac17c356f9272e5ef3e89ada70f2bb8fc3092d74978d383b9e'
