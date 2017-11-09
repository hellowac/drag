#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/25"

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
            area = pqhtml('td[width="756"][valign="top"]>table:first')
            self.domain = tool.get_domain(url)
            # pdata = self.get_pdata(area)
            
            # print area.outerHtml()
            # exit()

            #下架
            # if True :

                # log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                # self.logger.info(log_info)
                # data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                # return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = area('a[href^="brands_list.aspx"]:first').text()
            detail['brand'] = brand

            #名称
            detail['name'] = area('.product_details_title').text()

            #货币
            if area('.ch_currency_details').text().strip()[0] == u'￥' :
                currency = 'CNY'
                detail['currency'] = currency
                detail['currencySymbol'] = tool.get_unit(currency)
            else :
                raise ValueError('get currency Fail')

            #价格
            price = listPrice = re.search(r'(\d+[\d\.]*)', area('.ch_currency_details').text().replace(',', '')).groups()[0]
            detail['price'] = price
            detail['listPrice'] = listPrice

            #产品ID
            productId = area('input[name="product_id"]').attr('value')
            detail['productId'] = productId

            #颜色
            # color = self.get_color(area)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = productId

            #图片集
            imgs = [self.domain+'/'+img.attr('src') for img in area('.thumbbox img').items()] + [self.domain+'/'+img.attr('src') for img in area('.product_details img').items()]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = [dict(name=self.cfg.DEFAULT_ONE_SIZE, id=self.cfg.DEFAULT_SIZE_SKU ,sku=self.cfg.DEFAULT_SIZE_SKU ,inventory=self.cfg.DEFAULT_STOCK_NUMBER)]

            #描述
            detail['descr'] = area('td[class="product_details"][align="left"]').text()

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

    

