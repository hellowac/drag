#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/19"

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
            area = pqhtml('#productview #main')
            domain = tool.get_domain(url)
            
            # exit()

            #下架
            # if True :

                # log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                # self.logger.info(log_info)
                # data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                # return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = self.get_brand(pqhtml)
            detail['brand'] = brand

            #名称
            detail['name'] = area('#name').text()

            #货币
            currency = pqhtml('div[id="doc"]').attr('currency')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #获取信息
            price,listPrice,sizes=self.get_info(area)

            #价格
            detail['price'] = price
            detail['listPrice'] = listPrice

            #产品ID
            productId = area('input#productid').attr('value')
            detail['productId'] = productId

            #颜色
            # color = self.get_color(area)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = productId

            #图片集
            imgs = [img.attr('data-hires') for img in area('#thumbs-anim img').items()]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = sizes

            #描述
            detail['descr'] = area('.product-details').text()

            #详细
            detail['detail'] = area('.product-details').text()

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


    def get_info(self,area):
        try:

            # print pqhtml.outerHtml()

            form = area('#buyform')

            pvid = form('#arypvid').attr('value')

            stock = form('#arystock').attr('value')

            text = form('#arysubtext').attr('value')

            price = PyQuery(form('#aryprice').attr('value') or 'None').text().replace(' ','')

            origprice =  PyQuery(form('#aryorigprice').attr('value') or 'None').text().replace(' ','')


            pvids = filter(lambda x : x,pvid.split('|'))
            texts = filter(lambda x : x,text.split('|')) or [self.cfg.DEFAULT_ONE_SIZE]
            prices = map(lambda x: re.search(r'(\d[\d.]*)',x.replace(',','')).groups()[0],filter(lambda x : x,price.split('|')))
            stocks = map(lambda x: x if int(x) else self.DEFAULT_STOCK_NUMBER,filter(lambda x : x,stock.split('|')))
            origprices = map(lambda x: re.search(r'(\d[\d.]*)',x.replace(',','')).groups()[0],filter(lambda x : x,origprice.split('|')))

            sizes = map(lambda x : zip(['sku','inventory','name','price','listPrice'],x),zip(pvids,stocks,texts,prices,origprices))
            sizes = map(lambda x : dict(x),sizes)

            price = max(prices)
            listPrice = max(origprices)

            if not sizes :
                raise ValueError,'Get size, price, info Fail'

            return price,listPrice,sizes

        except Exception, e:
            raise


    def get_brand(self,pqhtml):
        try:
            Jtxt = pqhtml('script').text()

            g = re.search(r'ProductView\', (.*?)\);',Jtxt,re.DOTALL)

            brand = ''
            if g :
                a = 'p='+g.groups()[0]
                # exec 'a='+g.groups()[0]
                exec a in globals()
                brand = filter(lambda x: x[0] == p['Name'][0],p['Tags'])[0]
            
            if not brand :
                raise ValueError,'Get Brand info Fail'

            return brand
        except Exception, e:
            raise



