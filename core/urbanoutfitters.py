#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/07"

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
            
            
            # print json.dumps(pdata)
            # exit()

            #前期准备
            pdata = self.get_pdata(url)

            #下架
            if not pdata:
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌,2016-12-16维护
            if pdata.get('onlUrban OutfittersOnly',False) :
                brand = 'Urban Outfitters'
            else :
                brand = pdata['brand'] or pqhtml('meta[itemprop="brand"]').attr('content') or 'Urban Outfitters'

            detail['brand'] = brand

            #名称
            detail['name'] = pdata['description']

            #信息
            info = self.get_info(pdata)

            #价格
            # price,listPrice = self.get_all_price(area)
            detail['price'] = info['price']
            detail['listPrice'] = info['listPrice']

            #货币
            currency = info['currency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #颜色
            color = info['color']
            detail['color'] = color
            detail['colorId'] = dict([ (key,key) for key in color.keys() ])

            #钥匙
            detail['keys'] = color.keys()

            #图片集
            imgs = self.get_imgs(pdata)
            detail['img'] = imgs[0] if isinstance(imgs,list) else dict([ (key,imgArr[0]) for key,imgArr in imgs.items() ])
            detail['imgs'] = imgs

            #产品ID
            productId = pdata['productId']
            detail['productId'] = productId

            #规格
            detail['sizes'] = info['sizes']

            #描述
            detail['descr'] = PyQuery(pdata['longDescription']).text() or PyQuery(pdata['longDescription']).text()

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

    def get_info(self,pdata):
        skusInfo = pdata['skusInfo']

        currency = [ u['currencyCode'] for u in skusInfo[0]['priceLists'] if u['siteId'][:4] == 'With'][0]

        saleFlag = pdata['customText1Value']

        # print json.dumps(pdata)

        saleOff = 0

        #是否 折扣
        if saleFlag :

            g = re.search(r'\+(\d+)% off',saleFlag.lower(),re.DOTALL) # or re.search(r'(\d+)% off',saleFlag.lower(),re.DOTALL)

            if g :
                # raise ValueError,'Get SaleOff number fail'

                offNum = float('0.'+g.groups()[0])
                saleOff = 1.0 - offNum

        sizes = {}
        color = {}
        prices = []
        listPrices = []

        for info in skusInfo :

            sku = info['skuId']

            cid = info['colorId']

            plist = [ (p['salePrice'],p['listPrice']) for p in info['priceLists'] if p['siteId'][:4] == 'With' ][0]

            price = plist[0]
            listPrice = plist[1]

            if saleOff :
                price = str(float(price) * saleOff)

            prices.append(str(price))
            listPrices.append(str(listPrice))

            obj = dict(name=info['size'],id=sku,sku=sku,price=price,listPrice=listPrice,inventory=info['stockLevel'])

            if cid not in sizes :
                sizes[cid] = [obj]
                color[cid] = info['color']
            else :
                sizes[cid].append(obj)

        return dict(sizes=sizes,color=color,currency=currency,price=max(prices),listPrice=max(listPrices))


    def get_imgs(self,pdata):
        colors = pdata['colors']

        pid = pdata['productId']

        imgs = dict([(color['colorCode'],[ 'http://images.urbanoutfitters.com/is/image/UrbanOutfitters/{pid}_{cid}_{v}?$xlarge$&defaultImage='.format(pid=pid,cid=color['colorCode'],v=v) for v in color['viewCode'] ] ) for color in colors ])

        return imgs

    def get_pdata(self,url):
        productId = re.search(r'id=([\d\w]+)\b',url,re.DOTALL).groups()[0]

        link = 'http://www.urbanoutfitters.com/api/v1/product/{id}?siteCode=urban'.format(id=productId)
        
        resp = self.session.get(link, verify=False)

        if resp.status_code == 200 :
            data = json.loads(resp.text)['product']
        elif resp.status_code == 404:
            data = False
        else:
            raise ValueError,'get JsonData Fail'

        return data

        

