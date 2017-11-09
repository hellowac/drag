#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/14"

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
            area = pqhtml('#container')
            domain = tool.get_domain(url)
            pdata = self.get_pdata(pqhtml,domain)
            
            # print area.outerHtml()
            # print json.dumps(pdata)
            # exit()

            #下架
            if not pdata['hasOrderableVariants'] :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = area('.product-meta').attr('data-brand')
            detail['brand'] = brand

            #名称
            detail['name'] = area('.product-meta').attr('data-productname')

            #货币
            currency = re.search(r's\["currencyCode"\]="(\w{3})";',pqhtml('script').text()).groups()[0]
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #获取信息.
            price,sizes = self.get_info(pdata)

            #价格
            detail['price'] = price

            ptxt = area('.pricenotebucket').text()
            listPrice = re.search(r'\d[\d\.]',ptxt).groups()[0] if ptxt else price

            detail['listPrice'] = listPrice

            #颜色
            status,color,imgs = self.get_color(pdata)
            detail['color'] = color
            detail['colorId'] = dict([(key,key) for key in color.keys()])

            #钥匙
            detail['keys'] = color.keys()

            #图片集
            detail['img'] = imgs[0] if isinstance(imgs,list) else dict([ (cId,imgArr[0]) for cId,imgArr in imgs.items() ])
            detail['imgs'] = imgs

            #产品ID
            productId = area('.product-meta').attr('data-pid')
            detail['productId'] = productId

            #规格
            detail['sizes'] = sizes

            #描述
            detail['descr'] = area('section.product-details .longdescription').text()

            #详细
            detail['detail'] = area('section.product-details').text()

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = status

            #返回链接
            detail['backUrl'] = resp.url

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)


            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise

    def get_color(self,pdata):
        try:
            
            color = dict()
            imgs = dict()
            status = dict()
            for cId,variant in pdata['styles'].items() :
                cName = variant['primaryGenericColor']
                imgsArr = [ img['URL'] for img in variant['zoomimages']]
                color[cId] = cName
                imgs[cId] = imgsArr

                if variant['sellable'] :
                    status[cId] = self.cfg.STATUS_SALE

                elif variant['preorder'] :
                    status[cId] = self.cfg.STATUS_PRESELL

                else :
                    raise ValueError,'pdata status Error, function : get_color.'

            return status,color,imgs

        except Exception, e:
            raise


    def get_info(self,pdata):
        try:
            
            prices = list()
            sizes = dict()
            for variant in pdata['variants'] :
                colorId = variant['styleNo']

                width = variant['attributes'].get('width')

                #编辑只要width为'D'的size.的鞋子.
                if width and width['value'] != 'D' :
                    continue

                sName = variant['attributes']['size']['displayValue']
                sValue = variant['attributes']['size']['value']

                inv = variant['availability']['ATS'] if variant['availability']['avStatus'] == 'IN_STOCK' else 0

                sId = variant['id']

                sListPrice = variant['pricemodel']['pricing']['salesPriceFormatted'][1:]

                #salesPrice不为空...
                if variant['pricemodel']['pricing']['salesPrice'] :

                    raise ValueError,'Variant Saleprice is not equal empty!! fix this bug'

                obj = dict(name=sName,inventory=inv,price=sListPrice,id=sId,sku=sId)

                if colorId not in sizes : 
                    sizes[colorId] = [obj]
                else :
                    sizes[colorId].append(obj)

                prices.append(float(sListPrice))

            return max(prices),sizes

        except Exception, e:
            raise


    def get_pdata(self,pqhtml,domain):
        try:

            pid = pqhtml('.product-meta').attr('data-pid')

            for ele in pqhtml('script').items() :
                if 'productGetVariants' in ele.text() :
                    subLink = re.search(r'productGetVariants: "(.*)",',ele.text()).groups()[0]

                    break
            else :
                raise ValueError,'Get variants interface fail '

            link = domain + subLink + '?pid={}'.format(pid)

            data = json.loads(self.session.get(link, verify=False).text)

            return data

        except Exception, e:
            raise


