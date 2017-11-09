#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/08/12"

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
            area = pqhtml('#product_addtocart_form')
            # domain = tool.get_domain(url)
            pdata = self.get_pdata(pqhtml)
            
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
            brand = 'Native Youth'
            detail['brand'] = brand

            #名称
            detail['name'] = brand +' '+area('.block-right .block-basic-info h3').text()

            #货币
            currency = pdata['ecommerce']['currencyCode']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            colorId,colorName = self.get_color(area)
            detail['color'] = colorName
            detail['colorId'] = colorId

            #图片集
            imgs = [ img.attr('src') for img in area('.block-left .block-product-gallery ul.slides img').items()]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #产品ID
            productId = area('input[name="product"]').attr('value')
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(area)

            #描述
            detail['descr'] = area('.block-right .accordion div:first').text()

            #详细
            detail['detail'] = area('.block-right .accordion div:eq(3)').text()

            #退换货
            detail['returns'] = area('.block-right .accordion div:last').text()

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url
            
            #返回的IP和端口
            if resp.raw._original_response.peer :
                detail['ip_port']=':'.join(map( lambda x:str(x),resp.raw._original_response.peer))

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)


            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise


    def get_pdata(self,pqhtml):
        for ele in pqhtml('script[type="text/javascript"]').items() :
            if 'dataLayer.push' in ele.text() :
                data = re.search(r'dataLayer\.push\((.*\})\);\s*Ajax',ele.text(),re.DOTALL).groups()[0]
                data = json.loads(data)
                break
        else :
            raise ValueError('get data Fail')

        return data


    def get_all_price(self,area):
        priceBlock = area('.block-basic-info .price-box')

        if len(priceBlock('.old-price')) > 0 :

            ptxt = priceBlock('.special-price .price').text()

            price = re.search(r'(\d[\.\d]*)',ptxt).groups()[0]

            ptxt = priceBlock('.old-price .price').text()

            listPrice = re.search(r'(\d[\.\d]*)',ptxt).groups()[0]

        elif 'regular-price' in priceBlock.text() :

            ptxt = priceBlock('.price').text()

            price = re.search(r'(\d[\.\d]*)',ptxt).groups()[0]

            listPrice = price

        return price,listPrice


    def get_color(self,area):
        colorBlock = area('.block-select-colour')

        if len(colorBlock('label')) > 1 :
            raise ValueError('native youth color number great than 1 , fix this bug')

        colorName = colorBlock('label:first').attr('title')
        colorId = colorBlock('label:first input').attr('value')

        if not colorId or not colorName :
            raise ValueError('get colorName or ColorId Faile {0}:{1}'.format(colorName,colorId))

        return colorId,colorName


    def get_sizes(self,area):

        for ele in area('script[type="text/javascript"]').items() :

            if 'var opConfig' in ele.text() :

                opConfig = re.search(r'var opConfig = new Product.Options\((\{.*\})\);',ele.text(),re.DOTALL).groups()[0]

                opConfig = json.loads(opConfig)

                break
        else :
            raise ValueError("Get size optionData Fail")

        sizeBlock = area('.block-select-size')

        sizes = list()
        for size in sizeBlock('label').items():

            ID = size('input').attr('value')

            indexId = str(re.search(r'\[(\d*)\]',size('input').attr('name')).groups()[0])

            fixed = opConfig[indexId][str(ID)]['type'] == 'fixed'

            inv = self.cfg.DEFAULT_STOCK_NUMBER if fixed else 0

            obj = dict(name=size('p').text(),id=ID,sku=ID,inventory=inv)

            sizes.append(obj)

        if not sizes :
            raise ValueError('get sizes fail')

        return sizes

    

