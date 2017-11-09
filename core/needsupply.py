#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/08/05"

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
            area = pqhtml('#product-old') or pqhtml('#product-new')
            domain = tool.get_domain(url)
            
            # print area.outerHtml().encode('utf-8')
            # exit()

            #下架
            if 'out of stock' in area('.product-out-of-stock').text().lower() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            pdata = self.get_pdata(area,pqhtml)

            detail = dict()

            #品牌
            brand = area.attr('data-brand')
            detail['brand'] = brand

            #名称
            detail['name'] = brand+' '+ area.attr('data-name')

            #货币
            currency = pqhtml('#header-currency>a').text() or 'USD'
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #产品ID
            productId = area('form input[name="product"]').attr('value')
            detail['productId'] = productId

            #颜色
            color,sizes = self.get_info(pdata)
            detail['color'] = color
            detail['colorId'] = {key:key for key in color.keys()} if isinstance(color,dict) else productId

            #钥匙
            if isinstance(color,dict) :
                detail['keys'] = color.keys()

            #图片集
            imgs = self.get_imgs(area)
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = sizes

            #描述
            detail['descr'] = area('.description').text() + area('.sizing').text()

            #详细
            detail['sizeFit'] = area('p.sizing').text()

            #退换货
            detail['returns'] = area('p.shipping').text()

            #模特信息
            detail['model'] = area('p.sizing').text()

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


    def get_imgs(self,area):
        jtxt = area('script').text()

        data = ''

        tmp = re.search(r'product_modal_gallery = (.*);',jtxt)

        if tmp :
            data = tmp.groups()[0]

        #新增于2016-11-18
        if not data :
            tmp = re.search(r'productGallery = (.*);',jtxt)
            data = tmp.groups()[0]
        
        if not data :
            raise ValueError('get imgs data fail')

        imgs = json.loads(data)

        return imgs


    def get_info(self,pdata):

        colorData = None
        sizeData = None
        for key,data in pdata['attributes'].items() :
            if data['code'] == 'colors' :
                colorData = data
            elif data['code'] == 'sizes' :
                sizeData = data

        if not colorData :
            raise ValueError('get color or size data Fail')

        #------color

        assert(len(colorData['options']) == 1)      #单颜色.

        color = dict()
        color2ProductIds = dict()
        for option in colorData['options'] :
            color[option['id']] = option['label']
            color2ProductIds[option['id']] = option['products']

        # one size
        if not sizeData :
            sizes = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=self.cfg.DEFAULT_SIZE_SKU,id=self.cfg.DEFAULT_SIZE_SKU)]

        else :
            #------sizes
            sizes = dict()
            for option in sizeData['options'] :
                for cid,cproducts in color2ProductIds.items() :
                    if (set(option['products']) & set(cproducts)) :

                        obj = dict(name=option['label'],sku=option['id'],id=option['id'],inventory=self.cfg.DEFAULT_STOCK_NUMBER)

                        if sizes.has_key(cid) :
                            sizes[cid].append(obj)
                        else :
                            sizes[cid] = [obj]

        return color,sizes


    def get_pdata(self,area,pqhtml):
        eles = area('script').items()

        data = ''

        for ele in eles :
            if 'spJsonConfig' in ele.text() :
                tmp = re.search(r'var spJsonConfig = (.*);\n',ele.text())

                if tmp :
                    data = tmp.groups()[0] 
                    break

        #新增于2016-11-18
        if not data :
            for ele in pqhtml('script').items() :
               if 'spJsonConfig' in ele.text() :
                data = re.search(r'var spJsonConfigNew = (.*);\n',ele.text()).groups()[0]
                break 

        if not data :
            raise ValueError('get data fail')

        return json.loads(data)


    def get_all_price(self,area):
        # print area.outerHtml().encode('utf-8')
        price = area.attr('data-price')
        ptxt = area('.price-desktop .original_price').text() or area('.product-price .original-price').text() or price

        if not ptxt :
            raise ValueError('get Price Fail')

        listPrice = re.search(r'(\d[\d\.]*)',ptxt).groups()[0]

        return price,listPrice


    

