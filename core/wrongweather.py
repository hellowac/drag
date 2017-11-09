#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/14"

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
            area = pqhtml('.detalheProdutos')
            domain = tool.get_domain(url)
            pdata = json.loads(pqhtml('script[type=\'application/ld+json\']').text())
            
            # print area.outerHtml()
            # exit()

            #下架
            if 'SOLD OUT' in area('.topOff').text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = pdata['brand']['name']
            detail['brand'] = brand

            #名称
            detail['name'] = pdata['name']

            #货币
            currency = pdata['offers']['priceCurrency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            listPrice = self.get_listPrice(area,currency)
            detail['price'] = pdata['offers']['price']
            detail['listPrice'] = listPrice

            #颜色多于2个...
            if len(area('#listaCores a')) > 1 :
            	raise ValueError,'color number is great than 1 , fix this bug : %s' % url

            #颜色
            detail['color'] = area('#listaCores a:first').text()
            detail['colorId'] = area('#listaCores a:first').attr('data-id')

            #图片集
            imgs = [ domain + a.attr('href')[1:] for a in pqhtml('.lightgalleryG .item a').items()]
            detail['img'] = pdata['image']
            detail['imgs'] = imgs

            #产品ID
            productId = area('a#btAddCarrinho').attr('data-id')
            detail['productId'] = productId

            # for ele in area('div#listaTamanhos a').items() :
            # 	print ele.text()

            #规格
            detail['sizes'] = [ dict(name=ele.text(),inventory=self.cfg.DEFAULT_STOCK_NUMBER,id=ele.attr('data-id'),sku=ele.attr('data-ref'),price=ele.attr('data-preco').split()[0]) for ele in area('div#listaTamanhos a').items() ] \
            					or [ dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,id=productId) ]
            #描述
            detail['descr'] = pdata['description']

            #详细
            detail['detail'] = area('.descMarca').text()

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


    def get_listPrice(self,area,currency):
        classSelector = '.{}'.format(currency)

        ptxt = area('form .precos {} .precoOld'.format(classSelector)).text() or area('form .precos {} #precoProtuto'.format(classSelector)).text()

        listPrice = re.search(r'(\d[\.\d]+)',ptxt).groups()[0]

        return listPrice



