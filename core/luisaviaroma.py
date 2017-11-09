#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/28"

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

            #下架
            if status_code == 404 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            if status_code != 200 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            #下架
            if not pqhtml('#data').text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('#pnlSoldOutContainer').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            # print pqhtml.outerHtml()
            # exit()

            #前期准备
            false = False
            true = True
            null = None
            data = pqhtml('#data>#item_resp>script').text()
            print pqhtml.outerHtml().encode('utf-8')
            # data = data.replace(';;','')
            data = re.search(r'(itemResponse = \{.*\});\s*$',data,re.DOTALL).groups()[0]

            #执行赋值脚本
            exec data
            pdata = itemResponse

            # print data
            # exit()
            # pdata = json.loads(data)

            # pinfo = json.loads(pqhtml('script[type="application/ld+json"]').text())

            #修改于 2016-09-21
            ptxt = pqhtml('script[type="application/ld+json"]').text()
            ptxt = ptxt.replace('} {','}###---###{')
            pinfo = eval(ptxt)

            #下架
            if not data or pdata['SoldOut']:

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            if not pdata['Pricing'] :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.GET_ERR.get('LUIPERR','ERROR'),backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #设计者
            detail['designer'] = pdata['Designer']['Description']

            #品牌
            detail['brand'] = pinfo['brand']['name']

            #名称
            detail['name'] = detail['brand'].decode('utf-8') + u' ' +pdata['ShortDescription'].decode('utf-8') 

            #货币符号
            currency,price,listPrice = self.get_all_price(pdata)
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            detail['price'] = price
            detail['listPrice'] = listPrice

            #图片
            imgsTmp = self.get_imgs(pdata)
            detail['img'] = dict([(cId,cArr[0]) for cId,cArr in imgsTmp.items()])
            detail['imgs'] = imgsTmp

            #规格
            preorder,color,sizes = self.get_sizes(pdata)
            detail['keys'] = color.keys()
            detail['color'] = color
            detail['sizes'] = sizes
            detail['colorId'] = dict([(key,key) for key in color.keys()])

            #产品ID
            detail['productId'] = pinfo['sku']

            #描述
            detail['descr'] = self.get_descr(pdata)

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            if preorder['presell'] :
                detail['status'] = self.cfg.STATUS_PRESELL            #预售
                detail['presellDate'] = preorder['presellDate']     #预售时间
            else :
                detail['status'] = self.cfg.STATUS_SALE               #现货

            #返回链接
            detail['backUrl'] = resp.url

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)

            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise


    def get_all_price(self,pdata):
        try:

            if pdata['LvrCookieResponse']:
                currencyId = pdata['LvrCookieResponse']['ViewCurrencyId']
            else:
                currencyId = pdata['Pricing'][0]['Prices'][0]['CurrencyId']

            for pric in pdata['Pricing'] :
                for pr in pric['Prices'] :
                    if pr['CurrencyId'] == currencyId :
                        price,oldPrice = pr['FinalPrice'],pr['ListPrice']
                        break
                else :
                    raise ValueError,'Get Price Fail'

            return currencyId,price,oldPrice

        except Exception, e:
            raise


    def get_sizes(self,pdata):
        try:
            maxOrderQty = pdata['MaxOrderQuantity']

            preorder = dict(presell=False,presellDate=None)
            sizes = {}
            colors = {}
            allSize = {}
            for colorItem in pdata['ItemAvailability'] :

                if colorItem['ColorAvailability'] :

                    for color in colorItem['ColorAvailability'] :
                        colorId = color['VendorColorId']
                        colorName = color['ComColorDescription']

                        #过滤已有的size,比如:http://www.luisaviaroma.com/61I-AFJ013?fromItemSrv=1
                        if colorId not in allSize or colorItem['SizeValue'] not in allSize[colorId] :

                            #构造colors
                            if colorId not in colors:
                                colors[colorId] = colorName

                            #预售数量,现货为0,不为0则说明预售
                            if color['PreOrderQuantity'] :
                                preorder['presell'] = True
                                preorder['presellDate'] = time.mktime(time.strptime(color['PreOrderDate'],"%d/%m/%Y"))  

                            #构造sizes , PreOrderQuantity 为预售数量
                            obj = dict(name=colorItem['SizeValue'],sku=colorItem['SizeId'],inventory=color['OrderQuantity'] or color['PreOrderQuantity'])

                            if colorId in sizes :
                                sizes[colorId].append(obj)
                            else :
                                sizes[colorId] = [obj]

                            #过滤已有size提供依据
                            if colorId in allSize :
                                allSize[colorId].append(obj)
                            else :
                                allSize[colorId] = [obj]

            return preorder,colors,sizes

        except Exception, e:
            raise


    def get_descr(self,pdata):
        descr = ' '.join(pdata.get('LongtDescription',pdata['LongDescription']).split('|'))
        madeIn = pdata['MadeIn']
        composition = pdata['Composition']

        return descr+' '+madeIn+' '+composition


    def get_imgs(self,pdata):
        try:
            # imgPath = self.protocol + '//images.luisaviaroma.com/Medium'
            # imgPath = self.protocol + '//images.luisaviaroma.com/Total'
            # imgPath = self.protocol + '//images.luisaviaroma.com/Big'
            imgPath = 'http:' + '//images.luisaviaroma.com/Zoom'

            imgs = {}

            for photo in pdata['ItemPhotos'] :
                path = imgPath+photo['Path']
                colorId = photo['VendorColorId']
                if colorId in imgs :
                    imgs[colorId].append(path)
                else :
                    imgs[colorId] = [path]

            if imgs :
                return imgs

            raise ValueError,'Get Imgs Fail'

        except Exception, e:
            raise



        