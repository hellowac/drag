#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/08"

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


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)


    #获取页面大概信息
    def multi(self, url):
        pass



    #获取详细信息
    def detail(self,url):
        try:

            pid = url[url.rindex('/')+1:]

            if not pid.isalnum() :
                raise ValueError,'please check link. eg: https://xx/products/25518320'

            api = 'https://www.shopspring.com/api/1/products/%s?_=%s' %(pid,str(int(time.time()*1000)))

            resp = self.session.get(api, verify=False)

            status_code = resp.status_code
            pqhtml = PyQuery(resp.text)

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
            
            #前期准备
            pdata = json.loads(resp.text)
            
            # print json.dumps(pdata)
            # exit()

            #下架
            if not pdata['inventory_count'] :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = pdata['author']['name']
            detail['brand'] = brand

            #名称
            detail['name'] = brand+' '+pdata['name']

            #货币
            currency = PyQuery(self.session.get(url, verify=False).text)('meta[property="product:price:currency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            detail['price'] = pdata['price']
            detail['listPrice'] = pdata['original_price']

            #颜色
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = pdata['id']

            #图片集
            imgs = [ d['url'] for d in pdata['images']] 
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #产品ID
            productId = pdata['id']
            detail['productId'] = productId

            #规格
            detail['sizes'] = [dict(name=i['size'],inventory=i['count'],sku=i['id']) for i in pdata['inventory']]

            #描述
            detail['descr'] = pdata['more_info']

            #品牌描述
            detail['brandDescr'] = pdata['author']['description']

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = url

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)

            return tool.return_data(successful=True, data=detail)


        except Exception, e:
            raise
            
