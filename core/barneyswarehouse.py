#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/08/12"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
from utils.tools import get_url_addr_and_params
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
            area = pqhtml('div.primary-content')
            domain = tool.get_domain(url)
            
            # print area.outerHtml().encode('utf-8')
            # exit()

            #下架
            # if True :

                # log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                # self.logger.info(log_info)
                # data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                # return tool.return_data(successful=False, data=data)

            detail = dict()


            #产品ID
            # productId = area('input.productId').attr('value')
            productId = pqhtml('span[itemprop="productID"]').attr('content')
            detail['productId'] = productId
            detail['productSku'] = productId
            detail['productCode'] = productId
            
            #品牌
            brand = pqhtml('span[itemprop="brand"]').attr('content')
            detail['brand'] = brand

            #名称
            detail['name'] = pqhtml('span[itemprop="name"]').attr('content')

            #货币
            currency = pqhtml('span[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            price = pqhtml('span[itemprop="price"]').attr('content')
            detail['price'] = price
            detail['listPrice'] = listPrice

            #一级分类
            detail['category'] = area('a[data-bigpopup="sizeChart"]').attr('data-category')

            #二级分类
            detail['subcategory'] = area('a[data-bigpopup="sizeChart"]').attr('data-sub-category')

            #描述
            detail['descr'] = pqhtml('span[itemprop="description"]').attr('content')

            #详细
            detail['detail'] = area('#collapseOne').text()

            #退换货
            detail['returns'] = area('#collapseFive').text()

            #颜色
            # color = self.get_color(area)
            detail['color'] = pqhtml('span[itemprop="color"]').attr('content')
            detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

            #图片集
            imgs = [ img.attr('src') for img in area('.product-image-carousel img.primary-image').items()]
            detail['img'] = pqhtml('span[itemprop="image"]').attr('content')
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = self.get_sizes(area)

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url
            
            #返回的IP和端口
            if resp.raw._original_response.peer :
                detail['ip_port']=':'.join(map( lambda x:str(x),resp.raw._original_response.peer))

            log_info = json.dumps(dict(time=time.time(), 
                                       productId=detail['productId'], 
                                       name=detail['name'], 
                                       currency=detail['currency'], 
                                       price=detail['price'], 
                                       listPrice=detail['listPrice'], 
                                       url=url))

            self.logger.info(log_info)


            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise

    def get_all_price(self,area):
        priceBlock = area('.picker_price_attribute')

        if len(priceBlock('.red-discountPrice')) :
            ptxt = priceBlock('.red-discountPrice').text()
            lptxt = priceBlock('.red-strike').text()
        else :
            ptxt = priceBlock('.red-discountPrice').text()
            lptxt = priceBlock('.red-strike').text()

        price = re.search(r'(\d[\,\.\d]*)',ptxt).groups()[0].replace(',','')
        lprice = re.search(r'(\d[\,\.\d]*)',lptxt).groups()[0].replace(',','')

        if not price or not lprice :
            raise ValueError('get Price Fail')

        return price,lprice


    def get_sizes(self,area):
        sizeBlock = area('.size-label .selector')

        sizes = list()

        if len(sizeBlock) :
            for ele in sizeBlock('a.sizePicker').items() :
                obj = dict(
                    name=ele.text(),
                    id=ele.attr('data-skuid'),
                    sku=ele.attr('data-skuid'),
                    inventory=ele.attr('data-onhand-quantity'),
                    price=ele.attr('data-sale-price'),
                    listPrice=ele.attr('data-list-price')
                )

                sizes.append(obj)
        elif not len(area('.size-label')) :

            sku = area('#add_item_cart_fp').attr('data-fpskuid')
            inventory = re.search(r'Only\s*(\d*)\s*items',area('.inventory-message').text()).groups()[0]

            sizes = [dict(
                name=self.cfg.DEFAULT_ONE_SIZE,
                id=sku,
                sku=sku,
                inventory=int(inventory),
            )]
        
        if not sizes :
            raise ValueError('get sizes Fail')

        return sizes










