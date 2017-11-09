#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/06"

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
            area = pqhtml('.product-view')

            # print area.outerHtml()
            # exit()

            #下架
            if len(area('p.out-of-stock')) > 0 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #名称
            detail['name'] = area('.product-name:First').text()

            #品牌
            detail['brand'] = area('p.gq-designer').text()

            #颜色
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR

            #图片集
            imgs = [img.attr('href') for img in area('.product-img-box div[id^="MagicToolboxSelectors"]>a').items()] or [area('div.MagicToolboxMainContainer a.MagicZoomPlus').attr('href')]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #货币
            try:
                ctxt = pqhtml('#select-currency option[selected="selected"]').attr('value')
                currency = re.search(r'currency/(\w+)/uenc',ctxt).groups()[0]

            except Exception, e:
                currency =  pqhtml('div[id=" GlobaleCurrency"]').attr('currency')


            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品ID
            productId = area('input[name="product"]').attr('value')
            detail['productId'] = productId
            detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

            #规格
            detail['sizes'] = self.get_sizes(area)

            #描述
            detail['descr'] = area('div.product-shop dl#collateral-tabs dd:first').text() + area('div.product-shop dl#collateral-tabs dd').eq(1).text()

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

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

            priceInfo = area('.price-info:first')

            pinfo = priceInfo.outerHtml()

            if 'old-price' in pinfo and 'special-price' in pinfo :
                ptxt = priceInfo('p.special-price .price').text().replace(',','')
                lptxt = priceInfo('p.old-price .price').text().replace(',','')
            else :
                ptxt = priceInfo('.price-box .price').text().replace(',','')
                lptxt = ptxt

            price = re.search(r'(\d[\.\d]*)',ptxt).groups()[0]
            listPrice = re.search(r'(\d[\.\d]*)',lptxt).groups()[0]

            return price,listPrice 
        except Exception, e:
            raise


    def get_sizes(self,area):
        Jtxt = area('div.product-view div.product-shop script').text()

        g = re.search(r'Product.Config\((.*?)\);',Jtxt,re.DOTALL)

        if g :
            config = g.groups()[0]
            config = json.loads(config)

            sizes = [{'name':size['label'],'inventory':self.cfg.DEFAULT_STOCK_NUMBER,'sku':size['id']} for size in config['attributes']['135']['options']]

        else :
            sizes = [{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':self.cfg.DEFAULT_STOCK_NUMBER,'sku':self.cfg.DEFAULT_SIZE_SKU}]

        return sizes
