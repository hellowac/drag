#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/28"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool,FreeProxy
import re
import json
import time
import requests


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)
        self.session.headers.update(Host='www.gilt.com')
        # self.session.headers.update({
        #     'Proxy-Connection': 'keep-alive',
        #     'Cache-Control': 'max-age=0',
        #     'Upgrade-Insecure-Requests': '1',
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        #     # 'Referer': 'http://www.gilt.com/sale/women',
        #     'Accept-Encoding': 'gzip, deflate, sdch',
        #     'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        # })

    #获取页面大概信息
    def multi(self, url):
        try:
            
            resp = self.session.get(url)

            status_code = resp.status_code
            pqhtml = PyQuery(resp.text or 'nothing')

            if status_code != 200:

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message='status_code Error', backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            elements = pqhtml("section article.product-look")

            plist = []

            for product in elements.items():

                obj = {}

                obj['url'] = product('a:first').attr("href")

                obj['img'] = product('picture img:first').attr("srcset")

                obj['name'] = product('hgroup.look-name').text()

                obj['price'] = product("span.price").text()

                plist.append(obj)

            log_info = json.dumps(dict(time=time.time(),count=len(plist),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            return tool.return_data(successful=True, data=plist)

        except Exception, e:
            raise


    #获取详细信息
    def detail(self,url):
        try:            
            resp = self.session.get(url,timeout=self.cfg.REQUEST_TIME_OUT)
            # resp = requests.get(url,headers=self.session.headers,timeout=self.cfg.REQUEST_TIME_OUT)
            # print self.session.headers
            # resp = requests.get(url,headers=self.session.headers,timeout=20)

            status_code = resp.status_code
            pqhtml = PyQuery(resp.text or 'nothing')

            # print resp.headers

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

            Jtxt = pqhtml('script').text()

            #下架
            if 'productDetails' not in Jtxt :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            pdata = self.get_pdata(Jtxt)

            #前期准备
            product = pdata['product']
            allLooks = product['allLooks']
            skuJournal = self.get_skuJournal(Jtxt)
            sizeAttribute = product['sizeAttribute'] if product.has_key('sizeAttribute') else {'values':[{'id':0,'value':self.cfg.DEFAULT_ONE_SIZE}]}
            colorAttribute = product['colorAttribute'] if product.has_key('colorAttribute') else {'values':[{'id':0,'value':self.cfg.DEFAULT_ONE_COLOR}]}

            #lookId 和 SkuArr 映射 
            # lookId2SkuArr = dict([(look['productLookId'],[Id['skuId'] for Id in look['skus']]) for look in allLooks])
            #lookId 和 ImgArr 映射
            lookId2ImgArr = dict([(look['productLookId'],['http:'+img['retinaQuickViewLookUrl'] for img in look['images']])for look in allLooks])
            #lookId 和 现价 映射, 多颜色多价格
            lookId2Price = dict([(look['productLookId'],look['pricing']['maxSkuSalePrice']['raw']) for look in allLooks])
            #lookId 和 原价 映射,多颜色多价格
            lookId2ListPrice = dict([(look['productLookId'],look['pricing']['maxSkuMsrpPrice']['raw']) for look in allLooks ])
            #lookId 和 skuArr 映射
            lookId2SkuArr = dict([(look['productLookId'],[Id['skuId'] for Id in look['skus']]) for look in allLooks])
            #sizeId 和 名称 映射  #{2000: u's', 2001: u'm', 2002: u'l', 2003: u'xl', 2004: u'xxl'}
            sizeId2Name = dict([(size['id'],size['value']) for size in sizeAttribute['values']])
            #colorId 和 名称 映射   #{1000: u'dark red', 1001: u'true navy'}
            colorId2Name = dict([(color['id'],color['value']) for color in colorAttribute['values']])
            #sku 和 有库存 映射
            sku2Inventory = self.get_sku2Inventory(skuJournal)
            #sku 和 无库存 映射
            sku2NoInventory = dict([(sku['skuId'],sku['numberUnitsForSale']) for sku in skuJournal['entries'] if sku['type'] == 'inventory' and sku['status'] == ['X','U']])
            #更新 库存 字典
            sku2Inventory.update(sku2NoInventory)
            #sku 和 现价 映射, 多size多价格.
            sku2Price = dict([(sku['skuId'],str(sku['salePrice']['raw'])) for sku in skuJournal['entries'] if sku['type'] == 'pricing' ])
            #sku 和 原价 映射, 多size多价格.
            sku2ListPrice = dict([(sku['skuId'],str(sku['msrpPrice']['raw'])) for sku in skuJournal['entries'] if sku['type'] == 'pricing' ])
            #skuId 和 sizeId 映射
            skuId2SizeId = dict([(sku['skuId'],sku['savId']) for sku in skuJournal['entries'] if sku['type'] == 'associate' and sku['attribute'] == 'Size'])
            #skuId 和 colorId 映射
            skuId2ColorId = dict([(sku['skuId'],sku['savId']) for sku in skuJournal['entries'] if sku['type'] == 'associate' and sku['attribute'] == 'Color'])
            #sku 和 sizeName 映射
            sku2SizeName = self.get_sku2SizeName(product,skuId2SizeId,sizeId2Name)
            #sku 和 colorName 映射
            sku2ColorName = self.get_sku2ColorName(product,skuId2ColorId,colorId2Name)
            #lookId 和 colorId 映射
            lookId2ColorId = self.get_lookIe2ColorId(lookId2SkuArr,skuId2ColorId)
            #lookId 和 colorName 映射
            lookId2ColorName = self.get_lookIe2ColorName(lookId2SkuArr,sku2ColorName)
            #lookId 和 size集合 映射
            lookId2Sizes = self.get_lookId2Sizes(lookId2SkuArr,sku2SizeName,sku2Inventory,sku2Price,sku2ListPrice)

            # print(json.dumps(sku2Price))
            # print(json.dumps(sku2ListPrice))
            # print(json.dumps(lookId2SkuArr))
            # print(json.dumps(sku2ColorName))
            # print(json.dumps(lookId2ColorName))
            # print(json.dumps(sku2SizeName))
            detail = dict()

            #只获取当前连接中的sku值
            try:
                lookId = None
                if '-' in url[url.rindex('/'):] :
                    lookId = url[url.rindex('/')+1:].split('-')[0]
                    lookIds = [int(lookId)]
            except Exception, e:
                    pass

            #钥匙
            detail['keys'] = lookId2SkuArr.keys()

            #只获取链接中lookId
            # detail['keys'] = lookIds or lookId2SkuArr.keys()

            #颜色
            detail['color'] = lookId2ColorName
            detail['colorId'] = lookId2ColorId

            #产品ID
            detail['productId'] = product['productId']

            #图片
            detail['img'] = dict([(lookId,imgArr[0]) for lookId,imgArr in lookId2ImgArr.items()])
            detail['imgs'] = lookId2ImgArr

            #规格
            detail['sizes'] = lookId2Sizes

            #价格
            detail['price'] = lookId2Price
            detail['listPrice'] = lookId2ListPrice

            #品牌
            brand = pdata['brand']['name']
            detail['brand'] = brand

            #名称
            detail['name'] = brand+' '+pdata['product']['name']

            #货币符号
            currency = pdata['defaultLook']['pricing']['currencyCode']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #退换货
            detail['returns'] = pdata['returnPolicy']['description']

            #描述
            dtxt = PyQuery(pdata['product']['description'])
            dtxt.remove('strong')
            detail['descr'] = dtxt.text()

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

    
    #获取数据
    def get_pdata(self,Jtxt):
        try:
        
            g = re.search(r'productDetails: (.*?)skuJournal',Jtxt,re.DOTALL).groups()[0]

            if g is not None :
                return json.loads(g.strip()[:-1])
            else :
                raise ValueError,'productDetails is None'

        except Exception, e:
            raise

    
    def get_skuJournal(self,Jtxt):
        try:
            
            skuJournal = re.search(r'skuJournal: (.*?)channelId',Jtxt,re.DOTALL)      #库存关系json

            if skuJournal is not None :
                return json.loads(skuJournal.groups()[0].strip()[:-1])
            
            raise ValueError,'skuJournal is None'

        except Exception, e:
            raise


    def get_sku2Inventory(self,skuJournal):
        #有库存的sku,且对应的库存
        return dict([(sku['skuId'],sku['numberUnitsForSale'] if 'numberUnitsForSale' in sku else self.cfg.DEFAULT_STOCK_NUMBER) for sku in skuJournal['entries'] if sku['type'] == 'inventory' and sku['status'] in ['F','X']])

        # entries中的type对应的类型:
            # inventory  库存  [skuId,status("F":"for_sale","R":"reserved","X":"sold_out","U":"unavailable"),numberUnitsForSale,type]
            # pricing    价格  [skuId,msrpPrice{raw,formatted},salePrice,shippingSurcharge,type]
            # associate(关系)  [savId,attribute(size,color),skuId,type]
            # select          [savId,type]
            # images     图片  [savId,images,type]
            # associate_look(关系)   [savId,lookId,type]


    def get_sku2SizeName(self,product,skuId2SizeId,sizeId2Name):
        try:
            if product.has_key('sizeAttribute'):          #不只有一个size

                return dict([(skuId,sizeId2Name[sizeId]) for skuId,sizeId in skuId2SizeId.items() if sizeId in sizeId2Name ])

            else: #只有一个size,One Size

                return {'oneSize':sizeId2Name[0]}

        except Exception, e:
            raise e


    def get_sku2ColorName(self,product,skuId2ColorId,colorId2Name):
        try:
            return dict([(skuId,colorId2Name[colorId]) for skuId,colorId in skuId2ColorId.items() if colorId in colorId2Name ])

            # if JsProduct.has_key('sizeAttribute'):          #不只有一个color
            #     return dict([(skuId,colorId2Name[colorId]) for skuId,colorId in skuId2ColorId.items() if colorId in colorId2Name ])
            # else:           #只有一个color,No info
            #     return {'oneColor':colorId2Name[0]}

        except Exception, e:
            raise


    def get_lookIe2ColorName(self,lookId2SkuArr,skuId2ColorName):
        try:
            # return [(lookId,set([ skuId2ColorName[sku] for sku in skuArr ])) for lookId,skuArr in lookId2SkuArr.items()]
            #lookId转换为颜色名称
            lookId2ColorName = {}
            for lookId,skuArr in lookId2SkuArr.items():
                colorSet = set([skuId2ColorName.get(sku,self.cfg.DEFAULT_ONE_COLOR) for sku in skuArr])
                assert (len(colorSet) == 1),'lookId2ColorName fault'
                lookId2ColorName[lookId] = colorSet.pop()

            return lookId2ColorName

        except Exception, e:
            raise


    def get_lookIe2ColorId(self,lookId2SkuArr,skuId2ColorId):
        try:
            # return [(lookId,set([ skuId2ColorId[sku] for sku in skuArr ])) for lookId,skuArr in lookId2SkuArr.items()]
            #lookId转换为颜色ID
            lookId2ColorId = {}
            for lookId,skuArr in lookId2SkuArr.items():
                colorSet = set([skuId2ColorId.get(sku,self.cfg.DEFAULT_ONE_COLOR) for sku in skuArr])
                assert (len(colorSet) == 1),'lookId2ColorId fault'
                lookId2ColorId[lookId] = colorSet.pop()

            return lookId2ColorId

        except Exception, e:
            raise


    def get_lookId2Sizes(self,lookId2SkuArr,sku2SizeName,sku2Inventory,sku2Price,sku2ListPrice):
        try:
            lookId2SizeArr = {}
            for lookId,skuArr in lookId2SkuArr.items() :
               lookId2SizeArr[lookId] = [{'name':sku2SizeName.get(sku,self.cfg.DEFAULT_ONE_SIZE),'inventory':sku2Inventory[sku] if sku in sku2Inventory else 0 ,'price':sku2Price[sku],'listPrice':sku2ListPrice[sku],'sku':sku,'id':sku} for sku in skuArr]

            return lookId2SizeArr

        except Exception, e:
            raise

