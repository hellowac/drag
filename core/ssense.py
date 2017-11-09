#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/29"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
import re
import json
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

            resp = self.session.get(url,verify=False)

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
            area = pqhtml('div.browsing-page-root').filter('.product-item')

            #下架:
            if area('input#soldout').attr('value') == 'true' or len(area('select')) == 0 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)
            
            detail = dict()

            #名称
            detail['name'] = area('h1.product-brand').text() + ' '+area('strong.product-name').text()

            #品牌
            detail['brand'] = area('h1.product-brand').text()

            #货币
            currency = area('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            detail['price'] = area('meta[itemprop="price"]').attr('content')
            detail['listPrice'] = re.search(r'(\d[.\d]*)',area('h1.product-price').text().replace(',',''),re.DOTALL).groups()[0]

            #描述
            detail['descr'] = area('p.product-description-text').text()

            #规格
            detail['sizes'] = self.get_sizes(area)

            #颜色
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR

            #图片集
            imgsTmp = [img.attr('data-src') for img in area('div.product-images-container img').items() ]
            detail['img'] = imgsTmp[0]
            detail['imgs'] = imgsTmp

            #产品ID
            productId = area('.product-description-container').attr('data-product-id')
            detail['productId'] = productId
            detail['colorId'] = productId
            

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


    def get_sizes(self,area):
        try:
            sizeElements = area('select#size>option[value!=""]')

            if len(sizeElements) > 0 :
                sizes=[]
                for opt in sizeElements.items() :
                    size = opt.text().replace('\\n','') if opt.text() else self.cfg.DEFAULT_ONE_SIZE
                    size = re.sub(r'\s+',' ',size,re.DOTALL)
                    inv = self.cfg.DEFAULT_STOCK_NUMBER if 'disabled' not in opt.outerHtml() else 0 
                    #只剩一个时下单加不了购物车
                    if 'Only one left' in size : inv = 0
                    if 'Two items left' in size : inv = 2
                    if 'Sold Out' in size : inv = 0

                    if u'—' in size :
                        size = size.split(u'—')[0].strip()

                    sku = opt.attr('value')

                    sizes.append(dict(name=size,inventory=inv,sku=sku,id=sku))

                return sizes
            
            raise ValueError,'sizeElements is None'

        except Exception, e:
            raise


    

