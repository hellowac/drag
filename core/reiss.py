#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/27"

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

            data = tool.get_error(code=status_code, message='status_code Error', backUrl=resp.url, html=pqhtml.outerHtml())
            
            return tool.return_data(successful=False, data=data)

        # area = pqhtml('.product_schema_wrapper>.page_width')
        area = pqhtml('.container-full--small-only .grid')

        if not area:
            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))
            self.logger.info(log_info)
            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        # print area.outerHtml().encode('utf-8')

        # exit()

        detail = dict()

        #名称
        detail['name'] = area('h1.product__title').text() +' '+ area('h2.product__desc').text() +' '+ area('span.product__desc').text()

        #颜色
        detail['color'] = area('span[itemprop="color"]').text()

        #图片集
        # imgsTmp = [ a.attr('href') for a in area('.product-gallery__imgholder a').items() ]
        # imgsTmp = [ a.attr('data-zoom-image') for a in area('.product-gallery__imgholder a').items() ]
        imgsTmp = [ img.attr('data-lazy') or img.attr('src') for img in area('.product-gallery__imgholder a img').items() ]
        detail['img'] = imgsTmp[0]
        detail['imgs'] = imgsTmp

        #货币 
        currency = area('meta[itemprop="priceCurrency"]').attr('content')
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        #现价
        price = area('meta[itemprop="price"]').attr('content')
        detail['price'] = price

        #原价
        # detail['listPrice'] = area('span[itemprop="standard_price"]').text().replace(',','')
        listPriceBlock = area('span.product__price--old')
        detail['listPrice'] = re.search(r'(\d[\.\d,]*)',listPriceBlock.text()).groups()[0].replace(',','') if len(listPriceBlock) else price

        productInfo = area('#product-info')
        #描述
        detail['descr'] = productInfo('#design').text()

        #品牌
        detail['brand'] = 'REISS'

        #产品ID
        productId = area('span[itemprop="productID"]').text()
        detail['productId'] = productId

        #颜色ID
        detail['colorId'] = productId

        #配送和退货
        detail['delivery'] = productInfo('#delivery').text()
        detail['returns'] = productInfo('#delivery').text()

        #设计
        detail['designer'] = productInfo('#design').text()

        #sizeFit
        detail['sizeFit'] = productInfo('#size').text()

        #fabric
        detail['fabric'] = productInfo('#care').text()

        #规格
        detail['sizes'] = [ dict(
                name=opt.text(),
                sku=opt('input').attr('value'),
                id=opt('input').attr('value'),
                inventory=self.cfg.DEFAULT_STOCK_NUMBER if opt.attr('class') != 'size_not_available' else 0 
            )
            for opt in area('form .product-attributes .product-sizes .product-sizes__item').items() if len(opt('input'))        #if 过滤没有库存的size.
        ]

        #没有sizes?
        if not detail['sizes'] :

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
            
            return tool.return_data(successful=False, data=data)


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




