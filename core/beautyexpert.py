#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/25"

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
            area = pqhtml('.product-area')
            domain = tool.get_domain(url)
            # pdata = self.get_pdata(area)
            
            # print area.outerHtml()
            # exit()

            #下架
            if 'In stock' not in area('p.availability').text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = area('meta[itemprop="brand"]').attr('content')
            detail['brand'] = brand

            #名称
            detail['name'] = area('h1[itemprop="name"]').text()

            #货币
            currency = area('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品ID
            productId = area('input[name="prodId"]').attr('value')
            detail['productId'] = productId
            self.productId = productId

            #获取信息
            color,price,listPrice,img,imgs,sizes = self.get_info(area)

            #钥匙
            if isinstance(color,dict) :
                detail['keys'] = color.keys()

            #价格
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            detail['color'] = color
            detail['colorId'] = productId if isinstance(color,basestring) else {key:key for key in color.keys()}

            #图片集
            detail['img'] = img
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = sizes

            #描述
            detail['descr'] = area('.js-prodInfo-description').text()

            #详细
            detail['detail'] = area('.js-prodInfo-details').text()

            #退货
            detail['returns'] = area('.js-prodInfo-delivery').text()

            #配送
            detail['delivery'] = area('.js-prodInfo-delivery').text()

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
            #多颜色
            if len(area('.product-variation')) :

                print '1111'

                if len(area('select#opts-4')) != 1 :
                    raise ValueError('option type is not 4 , fix this bug')

                values = { ele.attr('value'):ele.text().split('-')[-1].strip() for ele in area('select[name="option"] option[value!=""]').items() }
                variation = area('input[name="variation"]').attr('value')

                data = dict(selected=1,variation1=variation)
                postUrl = 'http://www.beautyexpert.com/variations.json?productId={}'.format(self.productId)

                img = dict()
                imgs = dict()
                sizes = dict()
                color = dict()
                price = dict()
                listPrice = dict()
                for value,label in values.items() :
                    data['option1'] = value
                    resp = self.session.post(postUrl,data=data)
                    variationData = json.loads(resp.text)
                    
                    pid = variationData['productId']                                #该id不可随便改变.否则导致和之前抓的不兼容.
                    color[pid] = label
                    price[pid] = PyQuery(variationData['price']).text()[1:]
                    listPrice[pid] = PyQuery(variationData['rrpDisplay']).text()[1:]
                    img[pid] = [ 'http://s4.thcdn.com/'+a['name'] for a in variationData['images'] if a['index'] == 0 and a['type'] == 'zoom' ][0]
                    imgs[pid] = [ 'http://s4.thcdn.com/'+a['name'] for a in variationData['images'] if a['type'] == 'zoom' ]
                    sizes[pid] = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,id=pid,sku=pid)]

            else :
                color = self.cfg.DEFAULT_ONE_COLOR
                price,listPrice = self.get_one_price(area)
                img = area('div.main-product-image a:first').attr('href')
                imgs = [ ele.attr('href').strip() for ele in area('ul.product-thumbnails a').items() ] 
                sizes = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,id=self.productId,sku=self.productId)]

            return color,price,listPrice,img,imgs,sizes

        except Exception, e:
            raise

    def get_one_price(self,area):
        try:
            priceBox = area('p.product-price').text()
            saveBox = area('.yousave').text()

            price = re.search(r'(\d[\.\d]+)',priceBox).groups()[0]

            if saveBox :
                save = re.search(r'(\d[\.\d]+)',saveBox).groups()[0]
                listPrice = str(float(price) + float(save))
            else :
                listPrice = price

            return price,listPrice

        except Exception, e:
            raise
