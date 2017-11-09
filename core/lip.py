#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/28"

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
            
            resp = self.session.get(url, verify=False)

            status_code = resp.status_code
            pqhtml = PyQuery(resp.text or 'nothing')
            
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

            #准备
            area = pqhtml('#main-content')

            #下架

            emptyBlock = pqhtml('.stock-empty')

            if emptyBlock and 'OUT OF STOCK' in emptyBlock.text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            #价格符号必须为€
            if area('p.price span').text() != u'€' :
                raise ValueError,u'Lip currencySymbol is fault not €'

            detail = dict()

            #名称
            detail['name'] = 'LIP'+' '+area('.info h2').text() + area('p.revision').text()

            #品牌
            detail['brand'] = 'LIP'

            #价格符号
            currency = 'EUR'
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #图片集
            imgsTmp = [ 'http://www.lip.fr'+img.attr('big') for img in area('.zoomWrapper img').items() ] + [ 'http://www.lip.fr'+a.attr('href') for a in area('div.scrolling2-content a').items()]
            detail['img'] = imgsTmp[0]
            detail['imgs'] = imgsTmp

            #描述
            detail['descr'] = area('.info-contents ul').text()

            #配送
            detail['delivery'] = area('.info-contents ul>li:last').text()

            #详情
            detail['detail'] = area('.info-contents ul>li:eq(1)').text()

            #产品ID
            ltxt = area('.info-contents ul>li:eq(1)').text()

            g = re.search(r'Réf\.\s*(\d*)',ltxt,re.DOTALL)

            if not g :
                g = re.search(r'reference : (\d+)\s*',ltxt)

            if not g :
                g = re.search(r'Watch reference\s*(\d+)',ltxt)
            
            if not g :
                g = re.search(r'(\d[\d\.]+)$',pqhtml('title').text())

            if not g :
                g = re.search(r'\s*(\d[\d\.]+)\s*',pqhtml('title').text())

            productId = g.groups()[0]
            detail['productId'] = productId
            detail['colorId'] = productId
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR

            #判断库存
            stockBlock = pqhtml('.stock').text()

            if stockBlock and 'QUICK' in stockBlock :
                inv = re.search(r'ONLY (\d+) PRODUCT',stockBlock).groups()[0]
            else :
                inv = self.cfg.DEFAULT_STOCK_NUMBER

            #规格
            detail['sizes'] = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=inv,sku=productId)]


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



    def get_all_price(self,area):
        try:
            ptxt = area('p.price').text().replace(',','')

            price = re.search(r'(\d[\d\.]*)',ptxt,re.DOTALL).groups()[0]

            price = float(price)/100

            return price,price

        except Exception, e:
            raise


        