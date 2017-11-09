#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/07"

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
            area = pqhtml('.product-detail-information')
            # domain = tool.get_domain(url)
            
            # exit()

            #下架
            # if area('div[itemprop="availability"]').text().strip() != 'Available' :
            #     data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
            #     return tool.return_data(successful=False, data=data)

            detail = dict()



            #品牌
            # brand = re.search(r'brand: \'(.*?)\',',pqhtml('script[type="text/javascript"]').text(),re.DOTALL).groups()[0]
            brand = pqhtml('.product-brand img:first').attr('alt').split()[0]
            detail['brand'] = brand

            #名称 ,最近修改,2016-09-30 16:36:32
            detail['name'] = area('.J_title_name').text() or area('.title-name').text()

            #货币
            currency = pqhtml('a#select_currency').text().split()[0]
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            # color = self.get_color(area)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

            #图片集
            imgs = [ a.attr('href') for a in pqhtml('.product-detail-preview .toolbar>li>a').items()]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #产品ID
            productId = area('.product-detail-selection-sku').text()
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(area)

            #描述
            detail['descr'] = area('#product-description-tab').text()

            #详细
            detail['detail'] = area('#product-description-tab').text()

            #退换货
            detail['returns'] = area('.product-directions').text()

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
            
            pid = area('a[data-product-id!=""]').attr('data-product-id')

            link = 'http://cn.feelunique.com/pt_catalog/index/checkQty?product_id={pid}'.format(pid=pid)

            in_stock = json.loads(self.session.get(link, verify=False).text)['status'] 

            inv = self.cfg.DEFAULT_STOCK_NUMBER if in_stock else 0

            return [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=inv,sku=pid)]

        except Exception, e:
            raise


    def get_all_price(self,area):
        try:

            price=area('.integers').text() + area('.decimals').text()

            ptxt=area('.font-family-open:last').text() or price

            listPrice=re.search(r'(\d[\d.]*)',ptxt,re.DOTALL).groups()[0]

            if not price or not listPrice :
                raise ValueError,'Get Price Fail'

            return price,listPrice

        except Exception, e:
            raise

