#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/24"

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

            if status_code == 404 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)
                

            if status_code != 200 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)
            
            JscriptTxt = pqhtml('script').text()

            pqhtml.remove('script').remove('style')

            area = pqhtml('div#product-summary')

            # print area.outerHtml().encode('utf-8')

            buttonTxt = area('#product-form .add-button').text()

            if u'售罄' in buttonTxt.lower() or u'sold out' in buttonTxt.lower():

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)


            detail = dict()

            #所有图片
            imgs = self.get_imgs(pqhtml)
            detail['imgs'] = imgs
            detail['img'] = imgs[0]

            #名称
            detail['name'] = area('h1.brand').text() +' '+ area('.name').text()

            #货币
            currency = area('span.regular-price').text().split()[0]
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            color, sizes = self.get_sizes(area)

            #颜色
            detail['color'] = color

            #sizes
            detail['sizes'] = sizes

            #下架:
            if isinstance(detail['sizes'],basestring) and detail['sizes'] == 'sold out' :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            #描述
            detail['descr'] = area('div#description').text() or pqhtml('#product-details .product-details-section').text()

            #品牌
            detail['brand'] = area('h1.brand').text()

            #产品ID
            prodId = area.attr('data-id')
            detail['productId'] = prodId
            detail['colorId'] = prodId

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url
            
            #返回的IP和端口
            if resp.raw._original_response.peer :
                detail['ip_port']=':'.join(map( lambda x:str(x),resp.raw._original_response.peer))

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)

            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise


    def get_color_old(self,area):
        try:
            es = area('div.color select>option')
            # print es.outerHtml().encode('utf-8')
            if len(es) > 0 :
                for ele in  es.items() :
                    if 'selected' in ele.outerHtml() :
                        return ele.text()

            return self.cfg.DEFAULT_ONE_COLOR

        except Exception, e:
            e.message += ('function : get_color')
            raise e


    def get_all_price(self,area):
        try:
            ptxt = area('span.sale-price').text().replace(',','')

            optxt = area('span.regular-price').text().replace(',','')

            if not ptxt : ptxt = area('span.regular-price').text().replace(',','')

            if ptxt :
                price = re.search(r'(\d[\d\.]*)',ptxt).groups()[0]


            if optxt :
                listPrice = re.search(r'(\d[\d\.]*)',optxt).groups()[0]

            if not price or not listPrice :
                raise ValueError,'price is None'

            return price, listPrice

        except Exception, e:
            e.message += ('function : get_all_price')
            raise e


    def get_sizes_old(self,area):
        # elements = area('div#sylius_cart_item_variant>div.radio')

        #2016-11-21 日修改节点获取:
        elements = area('form#product-form .hidden-xs>div.radio')

        # print area.outerHtml().encode('utf-8')

        # 2017-04-12 19:35:02 修改
        data = json.loads(area.attr('data-product').encode('utf-8'))
        # print json.dumps(data)

        if len(elements) > 0 :
            sizes = [{'name':ele('label').text(),
                      'sku':ele('input').attr('value'),
                      'id':ele('input').attr('value'),
                      'inventory':self.cfg.DEFAULT_STOCK_NUMBER if not ele('input').attr('disabled') else 0 
                      } 
                      for ele in elements.items()
                    ]
            return sizes
        elif len(area('span.sold-out-btn')) > 0 :
            return 'sold out'
        else :
            return [{'name':self.cfg.DEFAULT_ONE_SIZE, 'inventory':self.cfg.DEFAULT_STOCK_NUMBER,'sku':self.cfg.DEFAULT_SIZE_SKU,'id':self.cfg.DEFAULT_SIZE_SKU}]

        raise ValueError,'sizes eleements is None'

    def get_sizes(self, area):
        # 2017-04-12 19:35:02 补充
        data = json.loads(area.attr('data-product').encode('utf-8'))
        # print area.outerHtml().encode('utf-8')
        # print json.dumps(data)

        sold_out = data.get('sold_out_at', False)

        if sold_out :
            return 'sold out', 'sold out'

        variants = data['variants']

        sizes = []

        for variant in variants:
            stock = variant['on_hand']
            if stock:
                if variant['options']:
                    name = variant['options'][0]['value']  # 如 "options": [{ "option": { "presentation": "Size", "name": "Size" }, "value": "US 10.5" }]
                    sid = sku = variant['id']
                else:
                    name = self.cfg.DEFAULT_ONE_SIZE
                    sid = sku = self.cfg.DEFAULT_SIZE_SKU

                obj = dict(name=name, sku=sku, id=sid, inventory=stock)

                sizes.append(obj)
        
        if not sizes:
            raise ValueError('get sizes fail')

        return data['display_color'], sizes



    def get_imgs(self,pqhtml):
        imgElements = pqhtml('div#gallery ul.slides img')
        if len(imgElements) > 0 :
            return [img.attr('data-image-full') for img in imgElements.items()]

        raise ValueError,'ImgsElements is None'
