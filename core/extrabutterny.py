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
            area = pqhtml('.container div[id^="product-"]')
            pdata = self.get_pdata(pqhtml)
            
            # print area.outerHtml()
            # print imgArea.outerHtml()
            # print json.dumps(pdata)
            # exit()

            #下架
            if area('meta[itemprop="availability"]').attr('content') != 'in_stock' :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = pdata['data']['vendor']
            detail['brand'] = brand

            #名称
            detail['name'] = pdata['data']['title'] if pdata['type'] == 'select' else area('h1.product_name').text()

            #货币
            currency = area('meta[itemprop="currency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(pdata,area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            # color = self.get_color(area)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = pdata['data']['id']

            #图片集
            img,imgs = self.get_imgs(pdata,area)
            detail['img'] = img
            detail['imgs'] = imgs

            #产品ID
            productId = pdata['data']['id']
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(pdata,area)

            #描述
            detail['descr'] = pdata['data']['description'] if pdata['type'] == 'select' else area('li#tab1').text()

            #退货
            detail['returns'] = area('li#tab4').text()

            #详细
            detail['detail'] = area('ul.tabs-content').text()

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #预售
            if len(area('form#contact_form')) > 0 :
                detail['statu'] = self.cfg.STATUS_PRESELL


            #返回链接
            detail['backUrl'] = resp.url

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)

            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise

    def get_imgs(self,pdata,area):
        try:
            if pdata['type'] == 'select' :

                img = 'http:' + pdata['data']['featured_image']
                imgs = map(lambda x : 'http:'+x,pdata['data']['images'])

            else :
                imgs = map(lambda x : 'http:'+x,[ img.attr('data-src') for img in area('.product_slider li img').items() ])
                img = imgs[0]

            if not img or not imgs :
                raise ValueError,'Get imgs or img Fail'

            return img,imgs

        except Exception, e:
            raise


    def get_all_price(self,pdata,area):
        try:
            if pdata['type'] == 'select' :

                price,listPrice = (float(pdata['data']['price'])/100),(float(pdata['data']['compare_at_price_max'])/100)
                
                if not listPrice :
                    listPrice = (float(pdata['data']['price_max'])/100)

            else :
                price = area('span[itemprop="price"]').attr('content')
                lptxt = area('.was_price').text() or area('.current_price').text()

                listPrice = re.search(r'(\d[\d\.]+)',lptxt).groups()[0]

            if not price or not listPrice :

                raise ValueError,'Get price or list Price Fail price:%s listPrice:%s' %(price,listPrice)

            return price,listPrice

        except Exception, e:

            raise


    def get_sizes(self,pdata,area):
        try:

            if pdata['type'] == 'select' :
                sizes = list()
                color = set()

                for variant in pdata['data']['variants'] :

                    obj = dict(name=variant['option1'],
                               inventory=variant['inventory_quantity'],
                               id=variant['id'],
                               sku=variant['barcode'])                                #取variant['sku'],每个sku都一样的,其实就是productId

                    sizes.append(obj)
                    color.add(variant['option2'])

                if len(color) > 1 :
                    raise ValueError,'color quantity great than 1 , fix this bug'

                return sizes

            else :
                has_inventory = [ ele.attr('value') for ele in area('#product-select option[value!=""]').items() ]

                variants = pdata['data']['variants']

                sizes = list()
                for variant in variants :
                    obj = dict( name=variant['public_title'].split()[0],
                                price=float(variant['price']/100),
                                sku=variant['barcode'],                                #取variant['sku'],每个sku都一样的,其实就是productId
                                id=variant['id'],
                                inventory= self.cfg.DEFAULT_STOCK_NUMBER if str(variant['id']) in has_inventory else 0 )

                    sizes.append(obj)

                return sizes

        except Exception, e:

            raise


    def get_pdata(self,pqhtml):
        try:

            # print area.text()

            # exit()
            for ele in pqhtml('script').items() :
                if 'product-select' in ele.text() :

                    data = re.search(r'OptionSelectors\("product-select", \{ product: (.*?\}),\s*onVariantSelected',ele.text()).groups()[0]

                    result = dict(type='select',data=json.loads(data))
                    break
            else :
                for ele in pqhtml('head script').items() :
                    if 'var meta' in ele.text() :
                        data = re.search(r'var meta = (.*\});\n',ele.text()).groups()[0]

                        result = dict(type='meta',data=json.loads(data)['product'])
                        break
                else :
                    raise ValueError,'Get meta data Fail'

            return result

        except Exception, e:
            raise
 

