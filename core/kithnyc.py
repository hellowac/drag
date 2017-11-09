#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/07"

#0.1 初始版
from . import DragBase
from xml.dom import minidom
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
            # area = pqhtml('.caption-product')
            area = pqhtml('.product-single-section-main')
            imgArea = pqhtml('.slider')
            domain = tool.get_domain(url)
            pdata = self.get_pdata(pqhtml('head'))
            
            # print area.outerHtml().encode('utf-8')
            # exit()

            #下架
            # if len(area('#variant-listbox')) == 0 :

            #     log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            #     self.logger.info(log_info)

            #     data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

            #     return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = pdata['product']['vendor']
            detail['brand'] = brand

            #名称
            detail['name'] = area('h1[itemprop="name"]').text()

            #货币
            currency = pqhtml('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            # color = self.get_color(area)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = pdata['product']['id']

            #图片集
            # imgs = [ 'https:'+a.attr('src') for a in imgArea('img').items()]
            imgs = [ 'http:'+img.attr('src') for img in area('.super-slider-main img').items()]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #产品ID
            productId = pdata['product']['id']
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(pdata,area)

            #描述
            detail['descr'] = area('.product-single-details-dropdown').text()

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

    def get_sizes(self,pdata,area):

        # has_inventory = [ ele.attr('value') for ele in area('#variant-listbox option[value!=""]').items() ]

        #2016-12-16维护
        has_inventory = [ ele.attr('value') for ele in area('select[id="productSelect"] option[value!=""]').items() ]

        variants = pdata['product']['variants']

        sizes = list()
        for variant in variants :
            obj = dict( name=variant['public_title'],
                        price=float(variant['price']/100),
                        sku=variant['sku'],
                        id=variant['id'],
                        inventory= self.cfg.DEFAULT_STOCK_NUMBER if str(variant['id']) in has_inventory else 0 )

            sizes.append(obj)

        return sizes


    def get_all_price_old(self,area):
            
        block = area('div.title')

        ptxt = block('.actual-price').text()
        lptxt = block('.compare-price').text()
        
        if not lptxt :
           lptxt =  ptxt

        price = re.search(r'(\d[\d\.]+)',ptxt.replace(',','')).groups()[0]
        listPrice = re.search(r'(\d[\d\.]+)',lptxt.replace(',','')).groups()[0]

        return price,listPrice

    #2016-12-16维护
    def get_all_price(self,area):
        price = area('.product-single-header #ProductPrice').attr('content')
        lptxt = area('#ComparePrice').text()

        if lptxt :
            listPrice = re.search(r'(\d[\d\.]+)',lptxt.replace(',','')).groups()[0]
        else:
            listPrice = price

        return price,listPrice

    def get_pdata(self,head_area):
        for ele in head_area('script').items() :
            if 'var meta' in ele.text() :
                data = re.search(r'var meta = (.*\});\n',ele.text()).groups()[0]
                break
        else :
            raise ValueError,'Get meta data Fail'

        return json.loads(data)


