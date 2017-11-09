#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/10/12"

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
            area = pqhtml('#pdp-page')
            domain = tool.get_domain(url)
            
            # print area.outerHtml()
            # exit()

            #下架
            if not area :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()


            #产品ID
            productId = pqhtml('img[data-stylenumber!=""]').attr('data-stylenumber').split('_')[0]
            detail['productId'] = productId
            
            #品牌
            brand = 'Lululemon'
            detail['brand'] = brand

            #名称
            detail['name'] = area('h1.OneLinkNoTx').text()

            #货币
            currency = pqhtml('input#currencyCode').attr('value').strip()
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #描述
            detail['descr'] = self.get_descr(pqhtml,area)

            #详细
            detail['detail'] = area('#fabric').text()

            #退换货
            detail['returns'] = ''

            colorDriver,colorCount = self.get_pdata(pqhtml)

            #颜色
            img,imgs,color = self.get_color(area,colorCount)
            detail['color'] = color
            detail['colorId'] = { key:key for key in color}

            #图片集
            detail['img'] = img
            detail['imgs'] = imgs

            #规格
            sizes,price= self.get_sizes(colorDriver)
            detail['sizes'] = sizes
            detail['price'] = price

            if isinstance(color,dict) :
                detail['keys'] = [key for key in color]

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

    def get_pdata(self,pqhtml):
        
        for ele in pqhtml('script').items():
            if 'colorDriverString' in ele.text():
                colorDriverString = re.search(r'var colorDriverString = (\{.*\});\s*var',ele.text()).groups()[0]
                styleCountDriverString = re.search(r'var styleCountDriverString = (\{.*\});',ele.text()).groups()[0]

                colorDriver = json.loads(colorDriverString)
                colorCount = json.loads(styleCountDriverString)

                break
        else :
            raise ValueError('get colorDriver and colorCountFail .')

        return colorDriver,colorCount

    def get_all_price(self,area):

        price_block = area('.product-description .price-fixed') or area('.product-description .price-markdown')

        ptxt = price_block('.price-sale').text() if len(price_block('.price-sale')) else price_block.text()

        price = re.search(r'(\d[\d\.]*)',ptxt).groups()[0]

        lptxt = price_block('.price-original').text() if len(price_block('.price-original')) else price_block.text()

        listPrice = re.search(r'(\d[\d\.]*)',lptxt).groups()[0]

        if not price or not listPrice :
            raise ValueError('get price fail')

        return price,listPrice

    def get_descr(self,pqhtml,area):
        ginfo = area('#pdp-why-we-made-it').text()

        colorMap = {}

        for ele in pqhtml('script').items() :
            if 'var styleColorMap' in ele.text() :
                styleColorMap = re.search(r'var styleColorMap = (\[.*\]);',ele.text()).groups()[0]

                colorMap = json.loads(styleColorMap)
                break
        else:
            raise ValueError('get colorMap Fail')

        pinfos = {}

        for info in colorMap:
            colorId = info['colorId']
            txt = info['heroBannerHotSpotText']

            txt += ';\n'.join([ t['careDescription'] for t in info['care']])

            pinfos[colorId] = txt

        return pinfos

    def get_color(self,area,colorCount):
        
        color = dict()
        imgs = dict()
        img = dict()

        for ele in area('section.section-color-swatch span[id^="color-"]').items() :

            colorId = ele.attr('id').split('-')[-1]
            colorName = ele('img').attr('alt')

            stylenumber = ele('img').attr('data-stylenumber')
            imgPrefix = ele('img').attr('data-scene7url')+'{stylenumber}_{index}?$gsr-pdt-qrtr-lg$'

            imgs_ = [ imgPrefix.format(stylenumber=stylenumber,index=i) for i in range(1,int(colorCount[stylenumber][0][0]))]

            color[colorId] = colorName
            imgs[colorId] = imgs_
            img[colorId] = imgPrefix.format(stylenumber=stylenumber,index=1)

        if not color or not imgs or not img :
            raise ValueError('get color or imgs or img fail')

        return img,imgs,color

    def get_sizes(self,colorDriver):

        sizes = dict()
        prices = dict()

        for colorId,sinfos in colorDriver.items() :

            sizes[colorId] = list()
            prices[colorId] = list()

            for info in sinfos :
                sname,sku,price = info

                prices[colorId].append(float(price))
                sizes[colorId].append(dict(name=sname,sku=sku,price=price,listPrice=price,inventory=self.cfg.DEFAULT_STOCK_NUMBER))

        if not sizes :
            raise ValueError('get sizes fail')

        if not prices :
            raise ValueError('get sizes prices fail.')
        else :
            price = { colorId:max(price_) for colorId,price_ in prices.items() }

        return sizes,price

            


    

