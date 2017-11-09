#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/06"

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

            #错误
            if len(pqhtml('.error_message')) >= 1 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code,message=self.cfg.GET_ERR.get('SAKERR','ERROR'),backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)
            
            #前期准备
            area = pqhtml('#pdp-content-area')
            pdata = self.get_pdata(area)

            # print json.dumps(pdata)
            # exit()

            #下架
            if pdata['sold_out_message']['enabled'] or pdata['intl_shipping_restriction']['enabled'] :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = pdata['brand_name']['label'] if pdata['brand_name']['enabled'] else ''
            detail['brand'] = brand

            #名称
            detail['name'] = pdata['short_description']

            #货币
            currency = pdata['price']['list_price']['local_currency_code']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)
            
            #价格
            price,listPrice = self.get_all_price(pdata)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            color = dict([ (clor['id'],clor['label']) for clor in pdata['colors']['colors'] ])
            colorId = dict([ (clor['id'],clor['id']) for clor in pdata['colors']['colors'] ])
            detail['color'] = color
            detail['colorId'] = colorId

            #图片集
            imgs = self.get_imgs(pdata)
            detail['img'] = imgs[0] if isinstance(imgs,list) else dict([ (cid,Arr[0]) for cid,Arr in imgs.items() ])
            detail['imgs'] = imgs

            #钥匙
            detail['keys'] = color.keys()

            #产品ID
            productId = pdata['product_code']
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(pdata)

            #描述
            detail['descr'] = PyQuery(pdata['description']).text()

            #退换货
            detail['returns'] = pdata['simple_shipping_statement']['message']


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



    def get_all_price(self,pdata):
        price_ = pdata['price']

        price = price_['sale_price']['local_currency_value'].replace(',','').strip()
        oldPrice = price_['list_price']['local_currency_value'].replace(',','').strip()

        if price and oldPrice :
            return price,oldPrice

        raise ValueError,'Get price Fail'


    def get_sizes(self,pdata):

        colorArr = pdata['colors']['colors']
        sizeArr = pdata['sizes']['sizes']
        skuArr = pdata['skus']['skus']

        color = dict([(c['id'],{'value':c['label'],'out':c['is_soldout']}) for c in colorArr])
        size = dict([(s['id'],{'value':s['value'],'out':s['is_soldout']}) for s in sizeArr])
        # [{'sku':sku,'cid':cid,'sid':sid,'price':price,'oldPrice':oldPrice,'status':status}]
        # status : {available,waitlist}
        skus = [{'sku':s['sku_id'],'cid':s['color_id'],'sid':s['size_id'],'status':s['status_alias'],'price':s['price']['sale_price']['local_currency_value'].replace(',',''),'oldPrice':s['price']['list_price']['local_currency_value'].replace(',','')} for s in skuArr if s['status_alias'] == 'available']
        
        if not size :
            size = {-1:{'value':self.cfg.DEFAULT_ONE_SIZE,'out':True}}

        sizes = {}
        for sku in skus:
            cid = sku['cid']
            sid = sku['sid']
            status = sku['status']
            inv = 0 if status[:3] != 'ava' else self.cfg.DEFAULT_STOCK_NUMBER

            obj = dict(name=size[sid]['value'],price=sku['price'],oldPrice=sku['oldPrice'],sku=sku['sku'],inventory=inv)
            
            if cid in sizes :
                sizes[cid].append(obj)
            else :
                sizes[cid] = [obj]

        if sizes :
            return sizes

        raise ValueError,'Get Sizes Fail'


    def get_imgs(self,pdata):
            
        media = pdata['media']
        colors = pdata['colors']['colors']
        params = '?wid=900&hei=1200&fit=constrain'
        imgPath = 'http:'+media['images_server_url']+media['images_path']
        imageArr = media['images']

        imgs = {}

        #单颜色图片
        if len(colors) == 1 :
            cid = colors[0]['id']
            imgs[cid] = [ imgPath+code+params for code in imageArr]

        #多颜色图片
        elif len(colors) > 1 :
            for color in colors :
                cid = color['id']
                imgs[cid] = [imgPath+color['colorize_image_url']+params]
        else :
            raise ValueError,'Get Imgs Fail'

        return imgs


    def  get_pdata(self,area):
        Jtxt = area('script[type="application/json"]').text()

        if not Jtxt :
            raise ValueError , 'get details json Fail'

        productDetail = json.loads(Jtxt)['ProductDetails']

        assert(len(productDetail['main_products'])==1)

        productMain = productDetail['main_products'][0]

        return productMain
