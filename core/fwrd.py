    #!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/08/10"

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
            area = pqhtml('.fwd_page .fwd_content')
            # domain = tool.get_domain(url)
            # pdata = self.get_pdata(area)
            
            # print area.outerHtml().encode('utf-8')
            # print pqhtml.outerHtml()
            # exit()

            #下架
            if 'Sold Out' in area('.stock_info:first').text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = area('.product_info:first .designer_brand:first a:first').text() or area('.product_info:first .product-titles__brand a:first').text()
            detail['brand'] = brand

            #名称
            detail['name'] = brand + ' ' + (area('.product_info:first h2.product_name:first').text() or area('.product_info:first h1.product_name:first').text())

            #货币
            currency = pqhtml('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area('.eagle .prices'))
            detail['price'] = price
            detail['listPrice'] = listPrice

            #产品ID
            productId = area('button.addtobag').attr('data-code')
            detail['productId'] = productId

            #颜色
            detail['color'] = area('.color_dd .one_sizeonly').text() or area('.color_dd option:first').text()
            detail['colorId'] = productId

            #图片集
            imgs = [ a.attr('data-zoom-image') for a in area('.cycle-slideshow .product-detail-image-zoom img').items()]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = self.get_sizes(area)

            #描述
            detail['descr'] = area('#details').text()

            #品牌描述
            detail['brandDescr'] = area('#aboutdesigner').text()

            #退换货
            detail['returns'] = area('#free_ship_popup').text()

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


    def get_sizes(self,area):

        # print area.outerHtml().encode('utf-8')

        sizes = list()

        for opt in area('.size_dd #size-select option[value!=""]').items() :
            name = opt.text().strip()

            inv = 0

            if opt.attr('data-is-one-left') != 'false' :
                inv = 1 
            elif opt.attr('data-is-oos') == 'false' :
                inv = self.cfg.DEFAULT_STOCK_NUMBER 

            obj = dict(name=name,inventory=inv,sku=opt.attr('value'),id=opt.attr('value'))

            sizes.append(obj)

        if not sizes and len(area('.size_dd #one-size-div')) == 1 :

            inv = 1 if 'display:none' not in area('.product_info #one-left-div').attr('style') else self.cfg.DEFAULT_STOCK_NUMBER

            sizes = [dict(name=self.cfg.DEFAULT_ONE_SIZE,sku=self.cfg.DEFAULT_SIZE_SKU,id=self.cfg.DEFAULT_SIZE_SKU,inventory=inv)]

        if not sizes :
            raise ValueError('get sizes Fail')

        return sizes


    def get_all_price(self,priceBox):

        ptxt = priceBox('.discount_price').text() or priceBox('.prices_retail').text() or priceBox('.prices__markdown').text()

        lptxt = priceBox('.price').text() or priceBox('.prices__retail-strikethrough').text() or ptxt

        if not ptxt or not lptxt :
            raise ValueError('get price ,listPrice text Fail')

        price = re.search(r'(\d[\d\.]*)',ptxt.replace(',','')).groups()[0]
        listPrice = re.search(r'(\d[\d\.]*)',lptxt.replace(',','')).groups()[0]

        if not price or not listPrice :
            raise ValueError('re search price or listPrice Fail')

        return price,listPrice


    

