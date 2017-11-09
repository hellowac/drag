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

            resp = self.session.get(url,verify=False)

            status_code = resp.status_code
            pqhtml = PyQuery(resp.text or 'nothing')

            domain = tool.get_domain(url)

            productId = re.search(r'.*\/(\d+)\/.*',url,re.DOTALL).groups()[0]

            link = domain + ('/ajaxprodDetail.aspx?ProdId=%s' % productId)
            
            resp = self.session.get(link,verify=False)
            
            #下架
            if status_code == 404 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            if status_code != 200 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            #前期准备
            pdata = json.loads(resp.text)

            # print json.dumps(pdata)

            #下架
            if pdata['Prods'] == []:

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)
            
            detail = dict()

            #品牌
            brand = pdata['Brand'].get('BrandLangName',None) or pdata['Brand']['DisplayBrandName']
            detail['brand'] = brand

            #名称
            currency = re.search(r'\(\'(\w{3})\'\)',pqhtml('a[onclick^="changeCurrency"]').attr('onclick'),re.DOTALL).groups()[0]
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #其他信息:

            detail['keys'] = []
            detail['name'] = dict()
            detail['sizes'] = dict()
            detail['price'] = dict()
            detail['img'] = dict()
            detail['imgs'] = dict()
            detail['descr'] = dict()
            detail['listPrice'] = dict()
            detail['color'] = dict()
            detail['colorId'] = dict()
            detail['productId'] = dict()

            for product in pdata['Prods'] :

                productId = product['ProdID']

                detail['keys'].append(productId)

                detail['productId'][productId] = productId
                detail['color'][productId] = self.cfg.DEFAULT_ONE_COLOR
                detail['colorId'][productId] = productId

                detail['name'][productId] = brand + ' ' +product['ProdLangName']

                detail['sizes'][productId] = [dict(name= product['OptionValue'],inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=product['OptionValue'])]

                detail['price'][productId] = re.search(r'(\d[\d\.]*)',PyQuery(product['ShopPrice']).text().replace(',',''),re.DOTALL).groups()[0]

                detail['listPrice'][productId] = re.search(r'(\d[\d\.]*)',PyQuery(product['WasPrice'] or product['ShopPrice']).text().replace(',',''),re.DOTALL).groups()[0]

                detail['img'][productId] = product['ProductImages'][0]['img700Src'] or product['ProductImages'][0]['img350Src'] or product['ProductImages'][0]['imgSrc']

                detail['imgs'][productId] = [ img['img700Src'] or img['img350Src'] or img['imgSrc'] for img in product['ProductImages']]

                detail['descr'][productId] = ' '.join([ descr.get('text') for descr in product['Description'] ])


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



    

