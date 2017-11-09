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
            
            #前期准备
            domain = tool.get_domain(url)
            pdata = self.get_pdata(pqhtml)
            pstore = self.get_pstore(pqhtml)
            pinfo = json.loads(pqhtml('script[type="application/ld+json"]').text())
            
            # print json.dumps(pdata)
            # exit()

            #下架
            # if True :
            #     data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
            #     return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = pinfo['brand']['name']
            detail['brand'] = brand

            #名称
            detail['name'] = brand+' '+pdata['name']

            #货币
            currency = pinfo['offers']['pricecurrency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            # price,listPrice = self.get_all_price(area)
            detail['price'] = pinfo['offers']['price']
            oldTmp = max([ size['oldPrice'] for colr in pdata['detail']['colors'] for size in colr['sizes']])
            detail['listPrice'] = oldTmp[:-2] if oldTmp else price

            #颜色
            color = dict([(c['id'],c['name']) for c in pdata['detail']['colors']])
            detail['color'] = color
            detail['colorId'] = dict([(c['id'],c['id']) for c in pdata['detail']['colors']])

            #钥匙
            detail['keys'] = color.keys()

            #图片集
            imgs = [ i.attr('src') for i in pqhtml('script[type="application/ld+json"]').next()('img').items()]

            if len(detail['keys']) > 1 :
                imgs = self.get_imgs(pdata)

            detail['img'] = imgs[0] if isinstance(imgs,list) else dict([ (key,imgArr[0]) for key,imgArr in imgs.items() ])
            detail['imgs'] = imgs

            #产品ID
            productId = pdata['id']
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(pdata,pstore)

            #描述
            descr = (pdata['detail']['description'] or '') + pdata['detail']['longDescription']

            composition = map(lambda x : x['composition'][0]['name'],pdata['detail']['composition'])

            tmp = ' '.join(composition)

            descr += tmp

            detail['descr'] = descr

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


    def get_imgs(self,pdata):
        try:
            
            imgs = {}

            for c in  pdata['detail']['colors'] :
                link = 'http://static.massimodutti.net/3/photos{url}_{one}_{two}_{three}.jpg?t={t}'.format
                imgs[c['id']] = []

                three = 0
                # 图片是否可用标志，主要是Three参数
                flag = True
                for i in c['image']['aux'] :
                    params=dict(url=c['image']['url'],t=c['image']['timestamp'],one=2,two=i,three=three)
                    imglink = link(**params)

                    while flag :
                        three += 1
                        params=dict(url=c['image']['url'],t=c['image']['timestamp'],one=2,two=i,three=three)
                        imglink = link(**params)
                        response = self.session.get(imglink)
                        flag = response.status_code != 200

                    imgs[c['id']].append(imglink)

            return imgs
        except Exception, e:
            raise



    def get_sizes(self,pdata,pstore):
        try:
            link = 'http://www.massimodutti.cn/itxrest/1/catalog/store/{id}/{catalog}/product/{pid}/stock'.format

            link = link(id=pstore['id'],catalog=pstore['catalogs'][0]['id'],pid=pdata['id'])
            
            stockData = json.loads(self.session.get(link, verify=False).text)

            for data in stockData['stocks'] :
                if data['productId'] == pdata['id'] :
                    sku2inv = dict([(s['id'],self.cfg.DEFAULT_STOCK_NUMBER if s['availability'] == 'in_stock' else 0 ) for s in data['stocks'] ])
                    break
            else :
                raise ValueError,'Get stock info Fail'

            sizes = {}
            for c in  pdata['detail']['colors'] :
                sizes[c['id']] = [ dict(name=s['name'],sku=s['sku'],price=s['price'][:-2],inventory=sku2inv.get(s['sku'],0)) for s in c['sizes']]

            return sizes

        except Exception, e:
            raise


    def get_pstore(self,pqhtml):
        try:
            for e in pqhtml('script[type="text/javascript"]').items() :
                if 'Inditex.iStoreJSON' in e.text() :
                    g = re.search(r'Inditex.iStoreJSON = (.*?\});\s*Inditex.iStorePolicyTypes',e.text(),re.DOTALL)
                    data = json.loads(g.groups()[0])
                    break
            else :
                raise ValueError,'Get pStoreJSON Fail'

            return data

        except Exception, e:
            raise


    def get_pdata(self,pqhtml):
        try:

            for e in pqhtml('script').items() :
                if 'iXProductJSON' in e.text() :
                    g = re.search(r'Inditex.iXProductJSON = (.*?\});\s*Inditex.iXShippingMethodsJSON',e.text(),re.DOTALL)
                    data = json.loads(g.groups()[0])
                    break
            else :
                raise ValueError,'Get pdata Fail'

            return data

        except Exception, e:
            raise

