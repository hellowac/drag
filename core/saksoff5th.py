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
# import re
import time
# import traceback


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

        #其他错误
        if status_code != 200 :

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_error(code=status_code, message='status_code:{0},need 200, message:{1}'.format(status_code,self.cfg.GET_ERR.get('SCERR','ERROR')), backUrl=resp.url, html=pqhtml.outerHtml())

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

        #颜色,此处必须取color的id,虽然有为0的坑.但是下面价格是根据id来进行区分颜色的.
        color = { str(clor['id']) : clor['label'] for clor in pdata['colors']['colors'] }
        colorId = { str(clor['id']) : str(clor['id']) for clor in pdata['colors']['colors'] }
        detail['color'] = color or self.cfg.DEFAULT_ONE_COLOR
        detail['colorId'] = colorId or self.cfg.DEFAULT_COLOR_SKU

        #图片集
        imgs = self.get_imgs(pdata,area)

        detail['img'] = imgs[0] if isinstance(imgs,list) else dict([ (cid,Arr[0]) for cid,Arr in imgs.items() ])
        detail['imgs'] = imgs

        #规格,包括多颜色的price.listPrice
        sprice,slistPrice,sizes = self.get_sizes(pdata)

        #钥匙
        if sizes.keys():
            detail['keys'] = sizes.keys()
        elif color :
            detail['keys'] = color.keys()

        # self.logger.debug('price.keys()->{}'.format(price.keys() if isinstance(price,dict) else 'not dict'))
        # self.logger.debug('color.keys()->{}'.format(color.keys() if isinstance(color,dict) else 'not dict'))
        # self.logger.debug('sizes.keys()->{}'.format(sizes.keys() if isinstance(sizes,dict) else 'not dict'))
        # self.logger.debug('detail[\'keys\']->{}'.format(detail['keys'] if 'keys' in detail else 'not keys')) 

        #产品ID
        productId = pdata['product_code']
        detail['productId'] = productId

        # print price,listPrice
        # print sprice,slistPrice
        detail['sizes'] = sizes
        detail['price'] = sprice
        detail['listPrice'] = slistPrice

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



    def get_all_price(self,pdata):

        # print json.dumps(pdata)
            
        price_ = pdata['price']

        price = price_['sale_price']['local_currency_value'].replace(',','').strip()

        if '-' in price :
            price = price.split('-')[0].strip()

        listPrice = price_['list_price']['local_currency_value'].replace(',','').strip()

        if price and listPrice :
            return price,listPrice

        raise ValueError,'Get price Fail'


    def get_sizes(self,pdata):
        
        # print json.dumps(pdata)
        
        # colorArr = pdata['colors']['colors']
        sizeArr = pdata['sizes']['sizes']
        skuArr = pdata['skus']['skus']

        # color = dict([(str(c['id']),{'value':c['label'],'out':c['is_soldout']}) for c in colorArr])
        size = dict([(s['id'],{'value':s['value'],'out':s['is_soldout']}) for s in sizeArr])
        # [{'sku':sku,'cid':cid,'sid':sid,'price':price,'listPrice':listPrice,'status':status}]
        # status : {available,waitlist}

        #此处color_id必须str.因为有可能是 0 这个坑....
        skus = [
            {
                'sku':s['sku_id'],
                'cid':str(s['color_id']),
                'sid':s['size_id'],
                'status':s['status_alias'],
                'price':s['price']['sale_price']['local_currency_value'].replace(',',''),
                'listPrice':s['price']['list_price']['local_currency_value'].replace(',','')
            } 
            for s in skuArr if s['sku_id'] != 'DUMMY'
        ]
        
        price = dict()
        listPrice = dict()

        if not size :
            size = {-1:{'value':self.cfg.DEFAULT_ONE_SIZE,'out':True}}

        sizes = {}
        for sku in skus:
            cid = sku['cid']
            sid = sku['sid']
            status = sku['status']
            inv = 0 if status[:3] != 'ava' else self.cfg.DEFAULT_STOCK_NUMBER

            obj = dict(name=size[sid]['value'],
                    id=size[sid]['value'],
                    price=sku['price'],
                    listPrice=sku['listPrice'],
                    sku=sku['sku'],
                    inventory=inv)
            
            if sizes.has_key(cid) :
                sizes[cid].append(obj)
                price[cid].append(sku['price'])
                listPrice[cid].append(sku['listPrice'])
            else :
                sizes[cid] = [obj]
                price[cid] = [sku['price']]
                listPrice[cid] = [sku['listPrice']]

        #取每个size的最大值和最小值
        price = { cid: min(priceArr) for cid,priceArr in price.items() }
        listPrice = { cid: max(priceArr) for cid,priceArr in listPrice.items() }

        if not price or not listPrice or not sizes :
            raise Exception('Get Sizes Fail')

        return price,listPrice,sizes


    def get_imgs(self,pdata,area):
            
        media = pdata['media']
        colors = pdata['colors']['colors']
        params = '?wid=900&hei=1200&fit=constrain'
        imgPath = 'http:'+media['images_server_url']+media['images_path']
        imageArr = media['images']

        # print json.dumps(pdata)
        # print area.outerHtml().encode('utf-8')
        imgs = {}

        #单颜色图片,color Id 必须 str, 有可能为0 的这个坑.
        if len(colors) == 1 :
            cid = str(colors[0]['id'])
            imgs[cid] = [ imgPath+code+params for code in imageArr]

        #多颜色图片,color Id 必须 str, 有可能为0 的这个坑.
        elif len(colors) > 1 :
            for color in colors :
                cid = str(color['id'])
                imgs[cid] = [imgPath+color['colorize_image_url']+params]
        else :
            imgs = [ imgPath+code+params for code in imageArr]

        
        if not imgs :
            raise ValueError,'Get Imgs Fail'

        return imgs


    def  get_pdata(self,area):
        Jtxt = area('script[type="application/json"]').text()
        Jtxt1 = area('script[type="application/json"]:first').text()         #2016-12-06更新

        if not Jtxt :
            raise ValueError , 'get details json Fail ! area detail:{0}'.format(area.outerHtml())
        try:
            productDetail = json.loads(Jtxt)['ProductDetails']
        except Exception:
            productDetail = json.loads(Jtxt1)['ProductDetails']              #2016-12-06更新

        assert(len(productDetail['main_products'])==1)

        productMain = productDetail['main_products'][0]

        return productMain


