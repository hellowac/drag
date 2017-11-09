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
            area = pqhtml('.product-detail-container')
            domain = tool.get_domain(url)
            
            # print area.outerHtml()
            # exit()

            #下架
            if u'缺货' in area('#stock-status').text():

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = area('#brand:first span').text() or area('#brand a').text()
            detail['brand'] = brand

            #名称
            detail['name'] = area('#name').text()

            #货币
            currency = area('#price-currency').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

            #图片集
            imgs = [a.attr('data-large-img') for a in area('.image-container  .thumbnail-container img').items()] or [img.attr('src') for img in area('#iherb-product-zoom img').items()]
            imgs = imgs or [area('#product-image .product-summary-image a').attr('href')]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #产品ID
            productId = area('input[name="pid"]').attr('value')
            detail['productId'] = productId

            #规格
            stock_txt = area('#stock-status').text()

            inv = area('#ddlQty option:last').attr('value') if 'In Stock' in stock_txt or u'有库存' in stock_txt else 0
            detail['sizes'] = [dict(name=self.cfg.DEFAULT_ONE_SIZE, inventory=inv, id=productId,sku=productId)]

            #描述
            detail['descr'] = area('#product-specs-list li').text()

            #详细
            detail['detail'] = pqhtml('div[itemprop="description"]').text()

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


    def get_all_price(self,area):
        try:

            price = area('#super-special-price b').text() or area('#product-price .price').text()
            oldPrice = area('#product-msrp .price').text() 

            #还有试用价:
            #area('#trial-price .price b').text()

            if price and oldPrice:
                price = re.search(r'(\d[\d\.]*)',price).groups()[0]
                oldPrice = re.search(r'(\d[\d\.]*)',oldPrice).groups()[0]
            else :
                raise ValueError,'Get price and old price Fail, price:%s , oldPrice:%s .' %(price,oldPrice)

            return price,oldPrice

        except Exception, e:
            raise
