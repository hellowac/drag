#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/08/08"

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
            

            #下架
            if len(pqhtml('#itemOptions #addToBasketDisabled')) > 0 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            #前期准备
            area = pqhtml('#details') or pqhtml('#productPage')
            domain = tool.get_domain(url)
            pdata = self.get_data(pqhtml)
            
            # print area.outerHtml().encode('utf-8')
            # print pdata
            # exit()

            detail = dict()

            #品牌
            brand = re.search(r'brand: "(.*?)",',pdata).groups()[0]
            detail['brand'] = brand

            #名称
            detail['name'] = area('h1[itemprop="name"]').text()

            #货币
            currency = self.get_currency(pdata)
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(pdata,area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            # print area.outerHtml()

            #图片集
            img_area = area('#itemGallery') or area('#galleryBasic')        #2016-09-16 13:51:08 更新
            imgs = [img.attr('src') for img in img_area('img').items()]
            imgs = imgs or [img.attr('data-zoom-image') for img in area('#product-view .main-image img').items()]   # 2017-03-3更新
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #产品ID
            productId = area('.wishlistAdd').attr('data-sku') or area('#productPage').attr('data-sku')
            detail['productId'] = productId

            #颜色
            # color = self.get_color(area)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(area)

            #描述
            detail['descr'] = area('#itemInfo ul>li:first').text()

            #退换货
            detail['returns'] = area('#itemInfo ul>li:last').text()

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

        except Exception:
            raise


    def get_data(self,pqhtml):

        dataObject = re.search(r'var dataObject =\s*(\{.*?\});\s*',pqhtml('script').text(),re.DOTALL)

        if not dataObject :
            raise ValueError,'dataObject Is None'

        return dataObject.groups()[0]


    def get_currency(self,pdata):

        g = re.search(r'currency:"([\w]{3})"\n',pdata)

        if not g :
            raise ValueError,'currency gorups is None'
        
        return g.groups()[0]


    def get_all_price(self,pdata,area):
        price = re.search(r'unitPrice:\s*"(\d[\d\.]*)",',pdata).groups()[0]

        ptxt = area('div.itemPrices span.was').text()

        if ptxt :
            ptxt = re.search(r'(\d[.\d]*)',ptxt,re.DOTALL)
            if ptxt :
                listPrice = ptxt.groups()[0]
        else :
            listPrice = price

        if not price or not listPrice :
            raise ValueError,'Get price fail'

        return price,listPrice


    def get_sizes(self,area):

        sizeButtons = area('#productOptions #itemOptions .options>button')

        # print area.outerHtml()

        sizes = list()

        if sizeButtons :
            for button in sizeButtons.items():

                if 'out of stock' in button.attr('title').lower() or 'noStock' in button.attr('class') :
                    inv = 0
                else :
                    inv = self.cfg.DEFAULT_STOCK_NUMBER

                obj = dict(
                    name=button.text(),
                    inventory=inv,
                    sku=button.attr('data-sku'),
                    id=button.attr('data-sku'),
                )

                sizes.append(obj)

        else :

            sizes = [{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':0,'sku':self.cfg.DEFAULT_SIZE_SKU,'id':self.cfg.DEFAULT_SIZE_SKU}]

        return sizes

    

