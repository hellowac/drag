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
            self.domain = tool.get_domain(url)

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
            area = pqhtml('#content>#productContainer')
            pdata = self.get_pdata(pqhtml)

            # print area.outerHtml()

            # print json.dumps(pdata)
            # exit()

            #下架
            if not area or area('.productButtons #disabledAddtobasket') :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = 'COS'
            detail['brand'] = brand

            #名称
            detail['name'] = area('.productInfo h1:first').text()

            #货币
            currency = pqhtml('meta[property="og:price:currency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(pqhtml,area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            color = self.get_color(area)
            detail['color'] = color
            detail['colorId'] = dict([ (key,key) for key in color.keys() ])

            #图片集
            imgs = self.get_imgs(area)
            detail['img'] = imgs[0] if isinstance(imgs,list) else dict([ (cid,Arr[0]) for cid,Arr in imgs.items() ])
            detail['imgs'] = imgs

            #钥匙
            detail['keys'] = color.keys()

            #产品ID
            productId = area('input[data-product-identifier!=""]').attr('data-product-identifier')
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(area)

            #描述
            detail['descr'] = area('.productInfo>.infowrap>dl>dd:first').text()

            #退换货
            detail['returns'] = area('.productInfo>.infowrap>dl>dd:first').text()

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
            
            sizeDivs = area('div.PriceAttributeTable>div.productSizes')

            sizes = {}
            for div in sizeDivs.items() :
                cid = div.attr('data-colorid')
                sid = div('input').attr('value')
                inv = 'http://www.cosstores.com/us/product/GetVariantData?variantId={value}&lookID=null&image=-1'.format
                sizes[cid] = [
                    {
                    'name':label.text(),
                    'inventory':0 if self.any(['outOfStock','disabled'],label.attr('class')) else json.loads(self.session.get(inv(value=label('input').attr('value'))).text)['StockQuantity'] ,
                    'sku':label('input').attr('value'),
                    'id':label('input').attr('value')
                    }
                    for label in div('label').items()
                ]
            
            if sizes :
                return sizes 

            raise ValueError,'Get Sizes Fail'

        except Exception, e:
            raise


    def get_imgs(self,area):
        try:
            
            colorImgs = area('#productThumbnails>li>img')

            imgs = {}
            for img in colorImgs.items() :
                cid = img.attr('data-colorid')
                url = self.domain + img.attr('srcset').split(', ')[-1].split()[0].replace('_7_','_0_')

                if cid in imgs :
                    imgs[cid].append(url)
                else :
                    imgs[cid]=[url]

            if imgs :
                return imgs 

            raise ValueError,'Get Imgs Fail'

        except Exception, e:
            raise


    def get_color(self,area):
        try:
            
            colorLabels = area('div.PriceAttributeTable>div.productColors label')

            colors = {}
            for label in colorLabels.items() :
                name = label.text()
                cid = label('input').attr('value')
                colors[cid] = name

            if colors :
                return colors 

            raise ValueError,'Get colors Fail'

        except Exception, e:
            raise


    def get_all_price(self,pqhtml,area):
        try:

            price = area('div.PriceContainer').text().strip()

            if price :
                price = price[1:].replace(',','')

            listPrice = pqhtml('meta[property="og:price:amount"]').attr('content') or price

            return price,listPrice

            raise ValueError,'Get Price Fail'
            
        except Exception, e:
            raise


    def get_pdata(self,pqhtml):
        
        try:
            ptxt = pqhtml('script[type="application/ld+json"]:last').text()

            return json.loads(ptxt)
        except Exception, e:
            raise

    def any(self,iterable,value):
        for v in iterable :
            if v in value :
                return True

        return False
