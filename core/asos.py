#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/22"

from . import DragBase
from pyquery import PyQuery
from utils import tool
import re
import json
import time


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)

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
            area = pqhtml('.product-details')
            pdata = self.get_pdata(pqhtml)

            # print json.dumps(pdata)
            print area.outerHtml().encode('utf-8')
            # exit()

            #下架
            # isNoSize,官网配置无size选项,shippingRestrictionsVisible，官网配置限制配送商品.
            # pdata['shippingRestrictions']['shippingRestrictionsVisible']:
            # 从pdata中读取数据,下架了即都是库存为0

            detail = dict()

            #品牌
            brand = pdata['brandName']
            detail['brand'] = brand

            #名称
            detail['name'] = pdata['name']

            #货币
            currency = pdata['price']['currency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = pdata['price']['current'],(pdata['price']['rrp'] or pdata['price']['previous'])
            detail['price'] = price
            detail['listPrice'] = listPrice or price

            #颜色
            color,colorId,img = self.get_color(pdata)
            detail['color'] = color
            detail['colorId'] = colorId

            #图片集,每个加参数，宽度1000(大图)
            imgs = map(lambda x: x+'?wid=1000',filter(lambda x: x,[ Dic['url'] for Dic in pdata['images']]))
            detail['img'] = img
            detail['imgs'] = imgs

            #产品ID
            productId = pdata['id']
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(pdata)

            #描述
            detail['descr'] = area('.product-description').text()

            #详细
            detail['detail'] = area('.product-details').text()

            #品牌描述
            detail['brandDescr'] = area('.brand-description').text()

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
            try:
                return self.detail_old(url)
            except Exception, e:
                raise

    #获取sizes
    def get_sizes(self,pdata):

        stock_info = self.get_stock_info(pdata)

        variants = pdata['variants']

        sizes = list()

        for variant in variants :
            variantId = variant['variantId']

            inv = self.cfg.DEFAULT_STOCK_NUMBER if stock_info['stock'][variantId]['isInStock'] else 0
            inv = 1 if stock_info['stock'][variantId]['isInStock'] and stock_info['stock'][variantId]['isLowInStock'] else inv

            obj = dict(
                name = variant['size'],
                sku = stock_info['stock'][variantId]['sku'],
                id = variant['sizeId'],
                inventory=inv,
                price = stock_info['stock'][variantId]['price']
            )
            sizes.append(obj)

        if not sizes :
            raise ValueError('get sizes Fail')

        return sizes

    def get_stock_info(self,pdata):
        api = 'http://us.asos.com/api/product/catalogue/v2/stockprice'

        pid = pdata['id']

        params = dict(
            productIds=pid,
            store=pdata['store']['code'],
            currency=pdata['price']['currency'],
            )

        resp = self.session.get(api,params=params, verify=False)

        stocks = json.loads(resp.text)

        if not stocks :
            raise ValueError('get stock info fail')

        stock_info = dict()

        for res in stocks :
            if res['productId'] == pid :
                stock_info['productCode'] = res['productCode']
                stock_info['stock'] = { variant['variantId']:dict(sku=variant['sku'],
                                                                isInStock=variant['isInStock'],
                                                                isLowInStock=variant['isLowInStock'],
                                                                price=variant['price']['current']['value']) for variant in res['variants'] }
                break
        else :
            raise ValueError('get pid:{0}\'s stock info Fail'.format(pid))

        #stock_info :{productCode,stock:{sku,isInStock,isLowInStock,price}}
        return stock_info

    #获取颜色及主图片.
    def get_color(self,pdata):
        if len(pdata['colourImageMap']) > 1 :
            raise ValueError('colour number is great than 1.')

        color = pdata['colourImageMap'].keys()[0]

        for img in pdata['images'] :
            if img['isPrimary'] :
                colorName = img['colour']
                colorId = img['colourCode']
                primaryImg = img['url']
                break
        else :
            raise ValueError('get color colourCode Fail')

        return colorName,colorId,primaryImg


    #获取产品的js配置
    def get_pdata(self,pqhtml):
        for ele in pqhtml('script[type="text/javascript"]').items() :
            if 'Pages/FullProduct' in ele.text() :

                data = re.search(r'view\(\'(\{.*\})\',',ele.text()).groups()[0]
                
                data = json.loads(data)
                
                break
        else :
            raise ValueError('get product config fail!')

        return data


    #获取单个产品详细信息
    def detail_old(self, url):
        try:
            
            resp = self.session.get(url, verify=False)

            status_code = resp.status_code
            pqhtml = PyQuery(resp.text or 'nothing')

            #错误
            if status_code != 200:

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            product = self.get_product_cfg_old(pqhtml)

            #下架
            if product is None or product['AvailableSkus'] == 0 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            price,oldPrice = self.get_all_price_old(pqhtml,product)

            colors_tmp = self.get_colors_old(pqhtml)

            detail = dict()
            
            detail['name'] = product['ProductName']

            detail['brand'] = product['ProductBrand']

            detail['currencySymbol'] = tool.get_unit(product['ProductCurrency'])

            detail['currency'] = product['ProductCurrency']

            detail['descr'] = product['ProductDescription'].replace('&nbsp;','')

            detail['productId'] = product['ProductCode']

            detail['price'] = price

            detail['listPrice'] = oldPrice

            detail['keys'] = [ color['key'] for color in colors_tmp]

            detail['color'] = dict([(color['key'],color['name']) for color in colors_tmp])

            detail['colorId'] = dict([(color['key'],color['value']) for color in colors_tmp])

            #图片信息
            imgs_tmp = self.get_imgs_old(pqhtml)
            detail['imgs'] = imgs_tmp
            detail['img'] = dict([(name,links[0]) for name,links in imgs_tmp.items()])

            detail['sizes'] = self.get_size_old(pqhtml)

            detail['url'] = url

            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            detail['backUrl'] = resp.url

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)


            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise


    #获取产品所有size
    def get_size_old(self,pqhtml):
        try:
            
            JscriptTxt = pqhtml('script').text()

            Js_sizes = re.findall(r'arrSzeCol\w*\[\d*\] = new Array\((.*?)\);',JscriptTxt,re.DOTALL)

            sizes = {}
            for size in Js_sizes :
                size = size.replace(r'\042','\\"')
                Arr = json.loads('[{data}]'.format(data=size))

                sizeName = Arr[1].replace(r'\042','"')+((' - '+Arr[4]) if Arr[4] else '')
                if sizeName == 'No Size' : sizeName = self.cfg.DEFAULT_ONE_SIZE
                colorName = Arr[2].title()                                      #title()和imgs中的颜色进行比对
                sizePrice = Arr[5]
                sizeOldPrice = Arr[8]
                if sizeOldPrice == '0.00' : sizeOldPrice = Arr[6]               #原价
                sizeMarkdownPrice = Arr[7]                                      #减少价
                sizeSku = Arr[0]   

                obj = {
                        'name':sizeName,
                        'price':sizePrice,
                        'listPrice':sizeOldPrice,
                        'sku':sizeSku,
                        'id':sizeSku,
                        'inventory':self.cfg.DEFAULT_STOCK_NUMBER if Arr[3] == 'True' else 0 } #该size是否 available

                if colorName in sizes : 
                    sizes[colorName].append(obj)
                else :
                    sizes[colorName]=[obj]


            return sizes

        except Exception, e:
            e.message += ('function : get_size')
            raise e


    #获取所有图片
    def get_imgs_old(self,pqhtml):
        try:
            JscriptTxt = pqhtml('script').text()
            Js_imgs = re.findall(r'arrMainImage\[\d*\] = new Array\((.*?)\);',JscriptTxt,re.DOTALL)
            Js_imgs = Js_imgs + re.findall(r'arrThumbImage\[\d*\] = new Array\((.*?)\);',JscriptTxt,re.DOTALL)

            imgs = {}
            for img in Js_imgs :
                Arr = map(lambda x: x.replace('"','').strip(),img.split(','))
                if len(Arr) == 4 :
                    colorName = Arr[-1].title()                                #title()和size中的颜色进行比对.
                    imgSrc = Arr[2]
                    imgs[colorName] = [imgSrc]

            for img in Js_imgs :
                Arr = map(lambda x: x.replace('"','').strip(),img.split(','))
                if len(Arr) == 3 :
                    for arr in imgs.values() :
                        arr.append(Arr[2])

            return imgs
        except Exception, e:
            e.message += ('function : get_imgs')
            raise e


    #获取所有颜色
    def get_colors_old(self, pqhtml):
        try:
            colors = pqhtml(
                'div.select-style select[id$="Colour"]>option[value!="-1"]')

            return [{'key': opt.attr('value').replace('/', '').replace('.', '').replace(' ', '').replace('&', '').title(), 
                    'value': opt.attr('value'), 
                    'name': opt.text()} for opt in colors.items()]
        except Exception, e:
            e.message += ('function : get_colors')
            raise e


    #获取需要的所有价格
    def get_all_price_old(self,pqhtml,product):

        try:
            oldprice = pqhtml('div#containerProductPrice span.discounted-price').text()

            if oldprice :
                price = pqhtml('div#containerProductPrice span.outlet-current-price').text()
                if not price :
                    price = pqhtml('div#containerProductPrice span.previousprice').text()

                oldprice = oldprice.replace(',','')
                price = price.replace(',','')

                price = re.search(r'(\d[.\d]*)',price).groups()[0]
                oldprice = re.search(r'(\d[.\d]*)',oldprice).groups()[0]

            else :
                oldprice = price = product['ProductPriceInNetworkCurrency'].replace(',','')

            return price,oldprice

        except Exception, e:
            e.message += ('function : get_all_price')
            raise e


    #获取产品的js配置
    def get_product_cfg_old(self,pqhtml):
        JscriptTxt = pqhtml('script').text()

        gProduct = re.search(r'var Product =\s*(\{.*?\});',JscriptTxt,re.DOTALL) 

        if gProduct is None :
            return None

        if gProduct :
            return json.loads(gProduct.groups()[0])
        else :
            raise ValueError,'asos product cfg loads fail'
