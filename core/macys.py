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
            area = pqhtml('.product-detail-information')
            self.domain = tool.get_domain(url)
            pdata = self.get_pdata(pqhtml)

            productId = pdata['id']
            subData = self.get_subData(productId)
            
            # print json.dumps(pdata)
            # print json.dumps(subData)

            # exit()

            #下架
            if 'Product may be unavailable' in subData.get('errorMessage','') :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #产品ID
            detail['productId'] = productId
            detail['productSku'] = productId
            detail['productCode'] = productId
            
            #品牌
            brand = subData['productThumbnail']['brand']
            detail['brand'] = brand

            #名称
            detail['name'] = pdata.get('name','') or PyQuery(pdata['shortDescription']).text()

            #货币
            currency = pqhtml('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            # print json.dumps(pdata)

            #价格
            # price,listPrice = pdata['salePrice'],pdata.get('regularPrice',pdata['salePrice'])
            price,listPrice = self.get_all_price(pdata)
            detail['price'] = price or listPrice
            detail['listPrice'] = listPrice

            #描述
            detail['descr'] = pqhtml('#memberProductDetails').text()
            detail['descr'] = pqhtml('.product-details-content').text()

            #图片集
            imgs = self.get_imgs(subData)

            detail['img'] = imgs[0] if isinstance(imgs,list) else {cid:Arr[0] for cid,Arr in imgs.items()}
            detail['imgs'] = imgs

            #规格
            sizes = self.get_sizes_by_subdata(subData['availabilityMap'])
            detail['sizes'] = sizes

            # detail['keys'] = sizes.keys()     #size里面有的颜色,price里面没有,2016-11-27
            keys = price.keys() if isinstance(price,dict) else sizes.keys()
            keys = map(lambda x: x , keys)
            detail['keys'] = set(keys)

            #部分颜色没有图片。随机取一个图片,2016-11-27
            if isinstance(price,dict) :
                for colorName in price.keys():
                    if colorName not in detail['imgs'] :
                        detail['imgs'][colorName] = imgs.values()[0]        #[pdata['mainImageURL']]
                        detail['img'][colorName] = imgs.values()[0][0]      #pdata['mainImageURL']

            #颜色
            color = {color:color for color in sizes.keys()}
            detail['color'] = color
            detail['colorId'] = color

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

    def get_all_price(self,pdata):
        '''
            新的取价格方式
        '''
        # print json.dumps(pdata).encode('utf-8')
        priceBlock = pdata['colorwayPricingSwatches']

        # print json.dumps(pdata)

        allPrice = dict()
        allListPrice = dict()

        if priceBlock :
            for catePrice,listPriceItem in priceBlock.items():
                for colorName,infoItem in listPriceItem.items():
                    wasPrice = ([ label['value'][0] for label in infoItem['tieredPrice'] if 'Was' in label['label']] or [0])[0]
                    listPrice = ([ label['value'][0] for label in infoItem['tieredPrice'] if 'Reg' in label['label'] or 'Orig' in label['label']] or [wasPrice] )[0]
                    salePrice = ([ label['value'][0] for label in infoItem['tieredPrice'] if 'Sale' in label['label']] or [0])[0]

                    if not wasPrice and not listPrice and not salePrice and len(infoItem['tieredPrice']) == 1 :
                        salePrice = infoItem['tieredPrice'][0]['value'][0]

                    allPrice[colorName] = salePrice
                    allListPrice[colorName] = listPrice or salePrice

            if not allPrice or not allListPrice :
                raise Exception('get price or list Price Fail')
        else :

            #单商品单颜色处理
            infoItem = pdata['colorwayPrice']

            wasPrice = ([ label['value'][0] for label in infoItem['tieredPrice'] if 'Was' in label['label']] or [0])[0]
            listPrice = ([ label['value'][0] for label in infoItem['tieredPrice'] if 'Reg' in label['label'] or 'Orig' in label['label']] or [wasPrice] )[0]
            salePrice = ([ label['value'][0] for label in infoItem['tieredPrice'] if 'Sale' in label['label']] or [0])[0]

            if not wasPrice and not listPrice and not salePrice and len(infoItem['tieredPrice']) == 1 :
                salePrice = infoItem['tieredPrice'][0]['value'][0]

            allPrice = salePrice
            allListPrice = listPrice or salePrice

        return allPrice,allListPrice

    def get_pdata(self,pqhtml):

        ptxt = pqhtml('script#pdpMainData').text()
        nptxt = pqhtml('script#productMainData').text()

        if ptxt :
            return json.loads(ptxt)['productDetail']

        elif nptxt :
            return json.loads(nptxt)

        raise ValueError,'pdpMainData is Empty'

    def get_subData(self,productId):
        url = self.domain+'/shop/catalog/product/newthumbnail/json?productId={productId}&source=100'.format(productId=productId)

        response = self.session.get(url, verify=False)

        if response.status_code != 200 :
            raise ValueError,'get Newthumbnail Error'

        return response.json()

    def get_imgs(self,subData):
        
        scene7ImgServer = subData['scene7ImgServer']

        primaryImages = subData['productThumbnail']['colorwayPrimaryImages']
        additionalImages = subData['productThumbnail']['colorwayAdditionalImages']

        # img_url = '{server}/products/{imgSubfix}?wid=1320&hei=1616&fit=fit,1&$filterxlrg$'
        img_url = '{server}/products/{imgSubfix}?wid=600&hei=900&fit=fit,1&$filterxlrg$'

        imgs = {color:[img_url.format(server=scene7ImgServer,imgSubfix=subfix)] for color,subfix in primaryImages.items()}

        if imgs and additionalImages and isinstance(additionalImages,dict) :
            for color, subfixs in additionalImages.items():
                subImgs = map(lambda x: img_url.format(server=scene7ImgServer,imgSubfix=x),subfixs.split(','))
                imgs[color].extend(subImgs)

        if not imgs :
            raise ValueError('get imgs fail')

        return imgs

    def get_sizes_by_subdata(self,subData):
        
        sizes = {}
        # print json.dumps(subData)
        # exit()

        tmp_sizes = dict()


        for upcId,amap in subData.items() :
            upcCode = amap['UPC_CODE']
            sizeName = amap['SIZE']
            colorName = amap['COLOR']
            JsonPrice = json.loads(amap['UPC_COLORWAY_PRICE'])
            retailPrice = JsonPrice['retailPrice']
            originalPrice = JsonPrice['originalPrice']
            intermediatePrice = JsonPrice['intermediatePrice']
            saleEndDate = JsonPrice['saleEndDate'] if 'saleEndDate' in JsonPrice else ''
            price = retailPrice if retailPrice != '' else originalPrice 
            oldPrice = originalPrice
            inventory = self.cfg.DEFAULT_STOCK_NUMBER if amap['available'] == 'true' else 0

            obj = dict(
                id=upcCode,
                sku=upcCode,
                name=sizeName,
                price=retailPrice,
                listPrice=originalPrice,
                inventory=inventory,
            )

            if colorName in sizes :
                if sizeName not in tmp_sizes[colorName] :
                    sizes[colorName].append(obj)
                    tmp_sizes[colorName].append(sizeName)
            else :
                sizes[colorName] = [obj]
                tmp_sizes[colorName] = [sizeName]

        return sizes
    

    

