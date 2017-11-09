#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/08/05"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
try:
    import simplejson as json
except ImportError, e:
    import json
import re
import time
import urllib
import random
from .amazon_util import amazon_size_link_asinDetail


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)


    #获取页面大概信息
    def multi(self, url):
        pass


    #获取详细信息
    def detail(self,url):
        resp = self.session.get(url, verify=False)

        status_code = resp.status_code
        pqhtml = PyQuery(resp.text or 'nothing')
        #下架
        if status_code == 404 :

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
            
            return tool.return_data(successful=False, data=data)

        #其他错误
        if status_code != 200 :

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        pqhtml.remove('style')

        #amazon机器人检查
        if 'Robot Check' in pqhtml('title').text() :

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_error(code=status_code, message='amazon roboot check, waiting for not robot check', backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        #前期准备,页面布局判断.
        self.url = url
        self.domain = tool.get_domain(url)
        self.pqhtml = pqhtml

        leftCol = pqhtml('div#leftCol')
        rightCol = pqhtml('div#rightCol')
        centerCol = pqhtml('div#centerCol')

        # print leftCol.outerHtml()k

        #图书模块
        if len(leftCol('div#booksImageBlock_feature_div')) :
            # print '####Book'

            from .amazon_book import distill as book_distill

            #传入实例
            detail = book_distill(self,leftCol,rightCol,centerCol,pqhtml)

            #需要后续获取详细？
            detail['amazon_need_wait'] = self.need_wait

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url

        #商品中间布局
        elif not rightCol and not centerCol :
            # print '####Panel'
            actionPanel=pqhtml('#actionPanel>div:first')

            from .amazon_panel import distill as panel_distill

            detail = panel_distill(self,leftCol,actionPanel,pqhtml)

            #需要后续获取详细？
            detail['amazon_need_wait'] = self.need_wait

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url

        #商品常规布局
        else : 
            # print '####General'

            # from .amazon_general import nowait_distill as general_nowait_distill

            # #一次返回所有价格，库存详情
            # detail = general_nowait_distill(self,leftCol,rightCol,centerCol,pqhtml)

            from .amazon_general import wait_distill as general_wait_distill

            #不返回所有价格，库存详情
            detail = general_wait_distill(self,leftCol,rightCol,centerCol,pqhtml)

            #需要后续获取详细？
            detail['amazon_need_wait'] = self.need_wait

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url
        
        #日志记录
        log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                              'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

        self.logger.info(log_info)

        return tool.return_data(successful=True, data=detail)


    def size_link_detail(self,link):
        resp = self.session.get(link, verify=False)

        status_code = resp.status_code

        #下架
        if status_code == 404 :

            log_info = json.dumps(dict(time=time.time(),title='amazon asin Detail get fail, return status_code 404',url=url))

            self.logger.info(log_info)

            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=resp.text[:500])
            
            return tool.return_data(successful=False, data=data)

        #其他错误
        if status_code != 200 :

            log_info = json.dumps(dict(time=time.time(),title='amazon asin Detail get fail, return status_code {}'.format(status_code),url=url))

            self.logger.info(log_info)

            data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=resp.text[:500])

            return tool.return_data(successful=False, data=data)
        
        detail = amazon_size_link_asinDetail(resp)
        detail['status_code'] = status_code

        #日志记录
        log_info = json.dumps(dict(time=time.time(), productName=detail['productName'], url=link))

        self.logger.info(log_info)

        return tool.return_data(successful=True, data=detail)

