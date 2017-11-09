#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/05"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
try:
    import simplejson as json
except ImportError, e:
    import json

import re
import xmltodict
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

            
            #前期准备
            area = pqhtml('.product-area')

            #下架
            if 'Sold out' in area('p.availability').text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #名称
            detail['name'] = area('h1.product-title').text()

            #品牌
            detail['brand'] = area('meta[itemprop="brand"]').attr('content')

            #颜色
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR

            #图片集
            imgs = [ a.attr('href').strip() for a in area('.media li.list-item a').items()]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #货币
            currency = area('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品ID
            productId = area('.js-enhanced-ecommerce-data').attr('data-product-id')
            detail['productId'] = productId
            detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

            #规格
            detail['sizes'] = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=productId)]

            #描述
            detail['descr'] = area('div[itemprop="description"]').text()

            #详情
            detail['detail'] = area('div.product-more-details').text()

            #价格
            detail['price'] = area('meta[itemprop="price"]').attr('content')

            ptxt = area('p.price-rrp').text() or area('p.product-price').text()

            detail['listPrice'] = re.search(r'(\d[\d\.]+)',ptxt,re.DOTALL).groups()[0]

            #退换货
            detail['returns'] = area('div.product-delivery-returns').text()

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



