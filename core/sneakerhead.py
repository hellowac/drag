#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/04"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
import re
import json
import time
import xmltodict


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

            #前期准备:
            Jtxt = pqhtml('script').text()
            pdata = self.get_pdata(Jtxt)
            area = pqhtml('#detail-display-wrapper')

            #下架
            if not pdata :
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #名称
            detail['name'] = pqhtml('h2.detail-title').text()

            #品牌
            detail['brand'] = self.get_brand(area)

            #价格符号
            currency = pqhtml('meta[itemprop="priceCurrency"]:first').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #颜色
            detail['color'] = pqhtml('ul.detail-additional-info:first>li:last').text()

            #价格
            detail['price'] = pdata['Products']['Info']['BasePrice'].replace(',','')
            listPrice = pdata['Products']['Info']['OldPrice'].replace(',','')
            detail['listPrice'] = (pqhtml('span.strokeText>span.price').text() or pqhtml('div#detail-display-info-wrapper span.price').text())[1:]

            #图片集合
            imgsTmp = [li.attr('data-zoom') for li in pqhtml('div#detail-display-icon ul').children('li').items()]
            detail['img'] = imgsTmp[0]
            detail['imgs'] = imgsTmp

            #规格
            detail['sizes'] = self.get_sizes(pdata,area)

            #描述
            detail['descr'] = area('p.detail-description:first').text()

            #产品ID
            detail['productId'] = pdata['Products']['Info']['ParentProductId']
            detail['colorId'] = pdata['Products']['Info']['ParentProductId']

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


    def get_brand(self,area):
        brandKey = area('h2.detail-title').text().split()[0].lower()
        return {
            'sebago': 'Sebago',
            'adidas': 'Adidas',
            'asics': 'Asics Onitsuka Tiger',
            'radii': 'Radii',
            'timberland': 'Timberland',
            'saucony': 'Saucony',
            'pointer': 'Pointer',
            'native': 'Native',
            'puma': 'Puma',
            'nike': 'Nike',
            'generic': 'Generic Surplus',
            'supra': 'Supra',
            'creative': 'Creative Recreation',
            'pf': 'PF Flyers',
            'new': 'New Balance',
            'swims': 'SWIMS',
            'clarks': 'Clarks',
            'vans': 'Vans',
            'lrg': 'LRG',
            'converse': 'Converse',
            'dc': 'DC Shoes',
            'bucketfeet': 'BucketFeet',
            "levi's": "Levi's",
            'palladium': 'Palladium',
            'thorocraft': 'Thorocraft',
            'reebok': 'Reebok',
            'ateliers': 'Ateliers Arthur',
            'air': 'Air Jordan',
            'diadora': 'Diadora'
        }[brandKey]



    def get_sizes(self,pdata,area):
    
        allSizes = dict([ (li('input').attr('value'),li('label').text()) for li in area('ul#detail-all-size>li').items() ])

        checkSizes = [ p['OptionId'] for p in pdata['Products']['Product'] ]

        sizes = [ dict(name=sName,inventory=self.cfg.DEFAULT_STOCK_NUMBER if OptionId in  checkSizes else 0 ,sku=OptionId) for OptionId,sName in allSizes.items()]

        return sizes


    def get_pdata(self,Jtxt):
        skuXml = re.search(r'skuXml = \'(.*?)\';',Jtxt,re.DOTALL)
        checkUrl = re.search(r'checkProductInventory\(\'(.*?)\'\s*\+',Jtxt,re.DOTALL)

        if skuXml and checkUrl:
            url = checkUrl.groups()[0] + skuXml.groups()[0] + '.xml'
            response = self.session.get(url, verify=False)

            if response.text : 
                return xmltodict.parse(response.text)

            return None

        raise ValueError,'search skuXml Fault'
