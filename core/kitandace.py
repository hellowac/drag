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
            area = pqhtml('.page-content')
            domain = tool.get_domain(url)
            # pdata = self.get_pdata(pqhtml)

            # print area.outerHtml()

            # print json.dumps(pdata)
            # exit()

            #下架
            if area('div[itemprop="availability"]').text().strip() != 'Available' :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = 'Kit and Ace'
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
            color = self.get_color(area)
            detail['color'] = color
            detail['colorId'] = dict([ (key,key) for key in color.keys() ])

            #图片集
            imgs = self.get_imgs(area,domain)
            detail['img'] = imgs[0] if isinstance(imgs,list) else dict([ (cid,Arr[0]) for cid,Arr in imgs.items() ])
            detail['imgs'] = imgs

            #钥匙
            detail['keys'] = color.keys()

            #产品ID
            productId = area('.js-pdp-product-code').attr('data-product-id')
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(area)

            #描述
            detail['descr'] = area('.pdp-desc__description').text()

            #构造物
            detail['fabric'] = area('.pdp-info-components').text()

            #详细
            detail['detail'] = area('.productDetailsPageSection1').text()

            #退换货
            detail['returns'] = area('.productInfo>.infowrap>dl>dd:first').text()

            #模特信息
            detail['model'] = self.get_model(area,color.keys())

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
        uls = area('ul.pdp-actions__sizes')

        sizes = dict()
        for ul in uls.items() :
            code = ul.attr('data-color').split('-')[-1]
            sizeArr = [  dict(name=li.attr('data-size'),sku=li.attr('data-code'),inventory=self.cfg.DEFAULT_STOCK_NUMBER if li.attr('data-online') == 'inStock' else 1 if li.attr('data-online') == 'lowStock' else 0 ,price=li.attr('data-price')[1:], listPrice=li.attr('data-oldprice')[1:] or li.attr('data-price')[1:] ) for li in ul('li').items() ] 
            sizes[code] = sizeArr

        return sizes


    def get_color(self,area):
        lis = area('.pdp-actions__color li.pdp-actions__color__item')

        color = dict()
        for li in lis.items() :
            code = li.attr('data-color')
            colorName = li.attr('data-name')

            color[code] = colorName

        return color

    def get_all_price(self,area):
        block = area('div.pdp-actions__price')

        price = block('span[itemprop="price"]').attr('data-value')

        listPrice = (area('.pdp-actions__sizes__size').attr('data-oldprice') or area('.pdp-actions__sizes__size').attr('data-price'))[1:]

        return price,listPrice


    def get_imgs(self,area,domain):
        block = area('.pdp-panel .pdp-carousel>ul.pdp-carousel__carousel')

        imgs = dict()

        for ul in block.items() :
            # code = re.search(r'color_(\d+)',ul.attr('class')).groups()[0]
            # imgArr = [ domain + img.attr('src') for img in ul('img').items() ]
            code = ul.attr('data-color').split('-')[-1]        #2016-12-16维护
            imgArr = [ domain + img.attr('data-src') for img in ul('li').items() ]

            imgs[code] = imgArr

        return imgs


    def get_model(self,area,colorIds):
        model = area('.pdp-desc__info__model .js-pdp-model')

        modelInfo = dict()
        for ele in model.items() :
            code = ele.attr('data-code')[:-1]
            text = ele.text()

            if code in modelInfo :
                continue
            else :
                modelInfo[code] = text + ele.next().text()

        return modelInfo

