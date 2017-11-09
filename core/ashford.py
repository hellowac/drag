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
            domain = tool.get_domain(url)

            #下架:
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
            Jtxt = pqhtml('script').text()
            area = pqhtml('#container')
            pdata = self.get_pdata(Jtxt)
            domain = tool.get_domain(url)

            #下架
            # if not instock :
                # data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                # return tool.return_data(successful=False, data=data)

            # print area.outerHtml()
            # exit()

            detail = dict()

            #图片
            imgsTmp = [ domain + a.attr('href') for a in area('form#addToCart ul.alt_imgs:first>li>a').items()]
            detail['img'] = imgsTmp[0]
            detail['imgs'] = imgsTmp

            #名称
            detail['name'] = pdata['product']['name']

            #品牌
            detail['brand'] = area('form#addToCart a#sameBrandProduct').text()

            #价格
            detail['price'] = pdata['product']['unit_sale_price']
            detail['listPrice'] = pdata['product']['unit_price']

            #价格符号
            currency = pdata['product']['currency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品id
            productId = pdata['product']['id']
            detail['productId'] = productId

            #颜色
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = productId

            #规格
            detail['sizes'] = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=pdata['product']['stock'],sku=productId)]

            #描述
            detail['descr'] = area('.prod_desc').text() + ' '+ area('div#info_tabs>div.wrap>div#tab1_info').text()

            #详细
            detail['detail'] = area('#tab1_info').text()

            #品牌描述
            detail['brandDescr'] = area('#tab2_info').text()

            #保修
            detail['note'] = area('#tab5_info').text()

            #配送
            detail['delivery'] = area('#shippingData').text()

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

    def get_pdata(self,Jtxt):
        try:
            data = re.search(r'universal_variable = (\{.*?\})\s*\(window',Jtxt,re.DOTALL).groups()[0]

            return json.loads(data)

        except Exception, e:
            raise

    

