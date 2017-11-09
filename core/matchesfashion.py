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
            area = pqhtml('#pdpMainWrapper')
            # domain = tool.get_domain(url)

            # pdataTxt = pqhtml('#pdpShopTheLookJSONData').attr('data-stl-json')

            productId = pqhtml('input#currentProductId').attr('value')

            # print pdataTxt.encode('utf-8')

            # print json.dumps(pdata).encode('utf-8')

            # print area.outerHtml().encode('utf-8')
            # exit()

            #下架
            if not productId :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            pdata = self.get_pdata(productId)

            detail = dict()


            #产品ID
            detail['productId'] = productId
            detail['productSku'] = productId
            detail['productCode'] = productId
            
            #品牌
            brand = pdata['designerData']['name']
            detail['brand'] = brand

            #名称
            detail['name'] = pdata['name']

            #货币
            currency = pdata['priceData']['currencyIso']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = pdata['priceData']['value'],pdata['priceData']['wasPrice']
            detail['price'] = price
            detail['listPrice'] = listPrice or price

            #描述
            detail['descr'] = area('li.pdp-accordion__header').text()

            #颜色
            # color = self.get_color(area)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

            #图片集
            imgs = [ 'http:'+img.attr('src') for img in pqhtml('.gallery-panel__main-image-wrapper img').items()]
            detail['img'] = 'http:'+pdata['thumbnail'].replace('_thumbnail','_large')
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = self.get_sizes(pdata)

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url
            
            #返回的IP和端口
            if resp.raw._original_response.peer :
                detail['ip_port']=':'.join(map( lambda x:str(x),resp.raw._original_response.peer))

            log_info = json.dumps(dict(time=time.time(), 
                                       productId=detail['productId'], 
                                       name=detail['name'], 
                                       currency=detail['currency'], 
                                       price=detail['price'], 
                                       listPrice=detail['listPrice'], 
                                       url=url))

            self.logger.info(log_info)


            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise

    def get_pdata(self,productId):
        address = 'http://www.matchesfashion.com/ajax/p/{0}?_={1}'.format(productId,str(int(time.time()*1000)))     #js精确时间到毫秒

        resp = self.session.get(address, verify=False)

        if resp.status_code != 200 :
            raise Exception('get pata fail; address:{0}'.format(address))

        return resp.json()

    def get_sizes(self,pdata):
        variantOptions = pdata['variantOptions']

        sizes = list()
        for variant in variantOptions :
            obj = dict(
                name=variant['sizeData']['value'],
                id=variant['sizeData']['baseCode'],
                sku=variant['code'],
                inventory=variant['stock']['stockLevel'],
                code=variant['sizeData']['code'],
            )

            sizes.append(obj)

        if not sizes and pdata['isOneSize'] :
            sizes = [dict(name=self.cfg.DEFAULT_ONE_SIZE,id=self.cfg.DEFAULT_SIZE_SKU,sku=self.cfg.DEFAULT_SIZE_SKU,inventory=self.cfg.DEFAULT_STOCK_NUMBER)]

        if not sizes :
            raise Exception('get sizes fail')

        return sizes

    
    

