#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/23"

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
            
            resp = self.session.get(url, verify=False)

            status_code = resp.status_code
            pqhtml = PyQuery(resp.text or 'nothing')
            #下架
            if status_code == 404 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            if status_code != 200 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message='status_code Error', backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            area = pqhtml('.product-area')

            instock = area('meta[itemprop="availability"]').attr('content') == 'InStock'

            #下架
            if not instock or area('.cat-button').text() == 'Sold Out' :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            # print area.outerHtml()
            # exit()

            detail = dict()

            #图片
            detail['img'] = area('a.product-img-zoom-action').attr('href')
            detail['imgs'] = [ele.attr('href') for ele in area('div.main-product-image>a').items()]

            #名称
            detail['name'] = area('h1[itemprop="name"]').text()

            #品牌
            detail['brand'] = area('meta[itemprop="brand"]').attr('content')

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #价格符号
            currency = area('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品id
            prodId = pqhtml('input[name="prodId"]').attr('value')
            detail['productId'] = prodId

            #颜色
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = prodId

            #规格
            detail['sizes'] = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=prodId,id=prodId)]

            #描述
            detail['descr'] = area('.js-prodInfo-description').text()

            #注意:
            if len(area('.promotionalmessage')) > 1 :
                detail['note'] = area('.promotionalmessage').text()

            #详细
            detail['detail'] = area('.js-prodInfo-details').text()

            #退货和配送信息
            detail['returns'] = area('.js-prodInfo-delivery').text()
            detail['delivery'] = area('.js-prodInfo-delivery').text()

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url
            
            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)

            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise



    #获取所有价格
    def get_all_price(self,area):
        ptxt = area('span[itemprop="price"]').text() or area('span[class="price"]').text()

        price = re.search(r'(\d[\d\.]*)',ptxt).groups()[0]

        #计算未折扣价格
        txt = area('span[itemprop="offers"]').outerHtml()

        if 'yousave saving-percent' in txt :

            divisor = re.search(r'(\d*)%',txt).groups()[0]
            divisor = float(divisor)/100

            listPrice = float(price)/(1-divisor)

            listPrice = round(listPrice,2)

        else :
            listPrice = price

        return price,listPrice

