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

            #下架:
            if len(pqhtml('.detail-info-outStock')) > 0 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)


            #前期准备
            Jtxt = pqhtml('script').text()
            area = pqhtml('.product-area') or pqhtml('#PDPContainer .container')

            # print area.outerHtml().encode('utf-8')

            if not area or 'sold out' in (area('.soldOut').text() or '').lower():
                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            domain = tool.get_domain(url)

            productId = pqhtml('input#ProductId').attr('value')

            pdata= self.get_pdata(Jtxt,productId)

            # print json.dumps(pdata)
            # print area.outerHtml().encode('utf-8')

            detail = dict()

            #图片
            imgsTmp = [img.attr('data-zoom-image') for img in pqhtml('ul.js-sliderProductPage li a img').items()]
            detail['img'] = imgsTmp[0]
            detail['imgs'] = imgsTmp

            #名称
            detail['name'] = pdata['name']

            #品牌
            detail['brand'] = pdata['designerName']

            #价格
            detail['price'] = pdata['unit_sale_price']
            detail['listPrice'] = pdata['unit_price']

            #价格符号
            currency = pdata['currency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品id
            detail['productId'] = productId

            #颜色
            detail['color'] = pdata['color'] or self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(pdata,domain)

            #描述
            detail['descr'] = pdata['description'] + pqhtml('dl.product-detail-dl').text()

            #设计者
            detail['designer'] = pdata['designerName'] + pqhtml('div[data-tstid="Content_Designer"] p').text()

            #注意:
            if len(area('.promotionalmessage')) > 1 :
                detail['note'] = area('.promotionalmessage').text()

            #详细
            detail['detail'] = area('.js-prodInfo-details').text()

            #退货和配送信息
            detail['returns'] = pqhtml('div[data-tstid$="FreeReturns"] p').text()

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


    def get_color(self,pdata):
        if pdata :
            #---------------------目前发现官网都是一个颜色....有2种以上颜色请告知.

            colors = [ variation['options'] for variation in pdata['variations'] if variation['variation'] == 'Colour']

            color = dict([ (color['id'],color['name']) for color in colors[0] ])

        else :
            color = {self.cfg.DEFAULT_COLOR_SKU:self.cfg.DEFAULT_ONE_COLOR}

        return color


    def get_sizes(self,pdata,domain):
        subfolder = pdata['subfolder']
        product_id = pdata['id']
        product_storeId = pdata['storeId']
        product_categoryId = pdata['categoryId']
        designerId = pdata['manufacturerId']
        data = {
            'productId':product_id,
            'storeId':product_storeId,
            'sizeId':'',
            'categoryId':product_categoryId,
            'designerId':designerId,
        }
        try:
            url = domain+subfolder+'/product/GetDetailState'               #subfolder决定取英文还是其他语言.

            try:
                response = self.session.post(url,data=data)                 #尝试post
                productDetails = json.loads(response.text)
            except Exception, e:                                            #尝试get
                response = self.session.get(url,params=data, verify=False)
                productDetails = json.loads(response.text)

        except Exception, e:             
            url = domain+subfolder+'/product/ProductDetailsAsync'               #subfolder决定取英文还是其他语言.

            response = self.session.post(url,data=data)

            productDetails = json.loads(response.text)

        # print json.dumps(productDetails)

        try:
            pySizes = PyQuery(productDetails['Sizes'])

            #本店有库存的product.

            li_elements_local = pySizes('li[class="js-product-selecSize-dropdown"]')

            #其他店product库存信息.
            li_elements_otherInfo = pySizes('li.detail-selectSize-fromNewBoutique')

            #其他店有库存的product.
            li_elements_other = pySizes('li[class="js-product-selecSize-dropdown-otherStoreAvailable"]')

            #处理其他店库存.
            sizes = self.get_sizes_by_local_store(li_elements_local)

            sizes += self.get_sizes_by_other_store(li_elements_other,li_elements_otherInfo,domain)

            if sizes == [] :        # 售罄
                return [{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':0}]

            return sizes
        except KeyError as e:

            sizes = []

            SizesViewModel = productDetails['SizesInformationViewModel']

            inv = 1 if SizesViewModel['IsLowStock'] else self.cfg.DEFAULT_STOCK_NUMBER

            for size_ in SizesViewModel['AvailableSizes'] :
                obj = dict(
                    name = size_['Description'],
                    id = size_['SizeId'],
                    sku = size_['SizeId'],
                    inventory = inv,
                    price = size_['PriceInfo']['Price']
                )
                sizes.append(obj)

            return sizes
        


    def get_sizes_by_other_store(self,otherStore_elements,otherStoreInfo_elements,domain):
        sizes = []

        for ele in otherStore_elements.items() :
            sizepos = ele.attr('data-sizepos')
            sizename = ele('span.productDetailModule-dropdown-numberItems').text()
            sizeSku = self.cfg.DEFAULT_SIZE_SKU
            inv = 1                                                                                     #其他买手店默认库存为1
            attrElements = []

            for element in otherStoreInfo_elements.items() :
                sizeSku = element('a').attr('data-sizeid')
                
                if ' {sizepos} '.format(sizepos=sizepos) in element.attr('class') :
                    ptxt = element('span[data-tstid="itemsalesprice"]').text() or element('span.listing-price').text()
                    optxt = element('span[data-tstid="itemprice"]').text() or element('span.listing-price').text()

                    attrElements.append({

                        'price':re.search(r'(\d[.\d]*)',ptxt.replace(',','')).groups()[0],
                        'oldPrice':re.search(r'(\d[.\d]*)',optxt.replace(',','')).groups()[0],
                        'url':domain+element('a').attr('href'),
                        'sku':sizeSku}) 

            otherStoreAvailable = sorted(attrElements,key=lambda x: x['price'],reverse=True)            #排序取最大价格.
            otherStoreAvailable_oldprice = sorted(attrElements,key=lambda x: x['oldPrice'],reverse=True)            #排序取最大价格.

            sizes.append({
                'name':sizename,
                'inventory':inv,
                'price':otherStoreAvailable[-1]['price'],
                'minPrice':otherStoreAvailable[-1]['price'],
                'maxPrice':otherStoreAvailable[0]['price'],
                'listPrice':otherStoreAvailable_oldprice[-1]['oldPrice'],
                'minListPrice':otherStoreAvailable_oldprice[-1]['oldPrice'],
                'maxListPrice':otherStoreAvailable_oldprice[0]['oldPrice'],
                'url':otherStoreAvailable[0]['url'],
                'sku':otherStoreAvailable[0]['sku'],
                'id':otherStoreAvailable[0]['sku'],})
        return sizes


    def get_sizes_by_local_store(self,localStore_elements):
        sizes = [{'name':li('span.productDetailModule-dropdown-numberItems').text(),'inventory':li('span.productDetailModule-dropdown-leftInStock').text(),'sku':li('input.sizedesc').attr('value'),'id':li('input.sizedesc').attr('value')} for li in localStore_elements.items()]

        for sizeInv in sizes:
                inven_ = re.search(r'(\d+)',sizeInv['inventory'])
                sizeInv['inventory'] = int(inven_.groups()[0]) if inven_ != None else self.cfg.DEFAULT_STOCK_NUMBER
        return sizes


    def get_pdata(self,Jtxt,productId):
        try:
            
            universalVariable = re.search(r'window\.universal_variable = (\{.*?\});',Jtxt,re.DOTALL).groups()[0]
            universalVariable = json.loads(universalVariable)
        except AttributeError :
            universalVariable = {}

        universalVariablePage = re.search(r'window\.universal_variable\.page = (\{.*?\});',Jtxt,re.DOTALL).groups()[0]
        universalVariableProduct = re.search(r'window\.universal_variable\.product = (\{.*?\});',Jtxt,re.DOTALL).groups()[0]

        universalVariablePage = json.loads(universalVariablePage)
        universalVariableProduct = json.loads(universalVariableProduct)

        universalVariableProduct.update(universalVariablePage)

        if 'id' in universalVariableProduct and universalVariableProduct['id'] == productId :
            universalVariable = universalVariableProduct 
        elif ('id' not in universalVariable) or universalVariable['id'] != productId:
            raise ValueError,'id not in JsonData({universalVariable})'.format(universalVariable=universalVariable)

        return universalVariable

