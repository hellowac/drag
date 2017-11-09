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

            resp = self.session.get(url, verify=False)

            status_code = resp.status_code
            pqhtml = PyQuery(resp.text or 'nothing')

            #下架:
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
            area = pqhtml('div.item_pageDesign_pageGroup')

            #下架:
            if area('span[id^="InventoryStatus_OnlineStatus"]').attr('content') != 'in_stock' :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            # print area.remove('script').remove('style').outerHtml()
            # print area.outerHtml()
            # exit()
            
            detail = dict()

            #名称
            detail['name'] = area('div[id^="product_Name"]').text()

            #品牌
            detail['brand'] = area('div.namePartPriceContainer h2.main_header').text()

            #货币
            currency = area('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #图片集
            imgsTmp = [atag.attr('data-large') for atag in area('#ProductAngleImagesAreaList a').items() ]
            detail['imgs'] = imgsTmp
            detail['img'] = imgsTmp[0]

            #规格
            detail['sizes'] = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=self.cfg.DEFAULT_SIZE_SKU)]

            #描述
            detail['descr'] = self.get_descr(area)

            #产品ID
            productId = re.search(r'\s*(\d+)',area('.wow_id_link').text(),re.DOTALL).groups()[0]
            detail['productId'] = productId

            #颜色
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
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



    def get_descr(self,area):
        nextDiv = area.next()

        descr = nextDiv('p[id^="product_longdescription"]').text()

        if descr and '' in nextDiv('b').text() :
            return descr + nextDiv('table.descriptive_attributes').text()
        
        raise Exception('Get Descr fault')


    def get_all_price(self,area):
        ptxt = area('div.price_display div[id^="offerPrice"] span.price').text()

        price = re.search(r'(\d[.\d]*)',ptxt.replace(',',''),re.DOTALL).groups()[0]

        ptxt = area('div.price_display div.old_prices span.price').text()

        listPrice = re.search(r'(\d[.\d]*)',ptxt.replace(',',''),re.DOTALL).groups()[0]
        
        if price and listPrice :
            return price,listPrice

        raise Exception('getPrice By offerPrice is None')


    

