#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/13"

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
import demjson


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
            # area = pqhtml('td[align="left"][width="619"][valign="top"]')
            area = pqhtml('form#productForm #ProductDetailPage #ProductDetails')  #2016-12-15添加
            pdata = self.get_pdata(pqhtml)
            domain = tool.get_domain(url)
            
            # print area.outerHtml().encode('utf-8')
            # exit()

            #下架
            if 'SOLD OUT' in pqhtml('font').text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = pqhtml('input[id="Brand"]').attr('value')
            detail['brand'] = brand

            #名称
            detail['name'] = area('#DetailsHeading').text()

            #价格
            currency,price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #货币
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品ID
            productId = area('input[name="ChildID"]').attr('value')  #也是colorID,产品ID是area('input[name="MasterID"]').attr('value')
            detail['productId'] = productId

            #图片集
            imgs = self.get_imgs(productId,pdata)
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #颜色
            color = self.get_color(productId,pdata)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(productId,pdata)

            #描述
            detail['descr'] = area('#Description').text()

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

    #2016-12-16维修
    def get_color(self,colorId,pdata):
        children = pdata['children']

        for c in children :
            if c['c'] == colorId :
                colorName = c['v']
                break
        else :
            raise Exception('get colorName fail')

        return colorName

    def get_sizes_old(self,pqhtml):
        listRemain = re.search(r'listRemain = \'(.*?),\'',pqhtml('script').text(),re.DOTALL)

        if listRemain :
            listRemain = listRemain.groups()[0]
            listRemain = dict(map(lambda x: tuple(x.split(':')),listRemain.split(',')))
            return [{'name':name,'inventory':inv,'sku':name,'id':name} for name,inv in listRemain.items()]
        
        raise ValueError,'Get listRemain Fault'

    #2016-12-16维修
    def get_sizes(self,colorId,pdata):
        variants = pdata['variants']

        sizes = []
        for var in variants :
            if colorId == var['c'] :
                sizeName = None 
                sizeWidth = None
                for o in var['a'] :
                    if o['n'] == 'width' :
                        sizeWidth = o['v']

                    elif o['n'] == 'size' :
                        sizeName = o['v']

                if sizeName and sizeWidth == 'D':        #width:D 是标准的鞋宽度,只取标准的D宽度
                    sizes.append(
                                dict(
                                    id=var['v'],
                                    sku=var['v'],
                                    name=sizeName,
                                    inventory=self.cfg.DEFAULT_STOCK_NUMBER
                                )
                        )

        if not sizes :
            raise Exception('get sizes fail')

        return sizes


    def get_imgs_old(self,productId,domain):
        url = domain+'/larger_view.asp?style=%s' % productId

        subResponse = self.session.get(url, verify=False)
        
        if subResponse.status_code != 200 :
            raise ValueError,'Get Img Info Fault url:{url}'.format(url=subResponse.url)

        pyhtml = PyQuery(subResponse.text)

        imgs = map(lambda x: x.split(','),[ img.attr('onmouseover').replace('AltView(','').replace(');','').replace('\'','') for img in pyhtml('td a[href^="javascript:AltView"]').items()])
        
        imgs = [domain+'/products//%s_xl.jpg' % productId] + [domain+'/products/alt_views/%s_alt%s.jpg' % (productId,img[0]) for img in imgs if img[0] != '0']

        if imgs : 
            return imgs

        raise ValueError,'get Imgs Fault'

    #2016-12-16维修
    def get_imgs(self,colorId,pdata):
        images = pdata['images']

        colorImgs = []
        for obj in images :
            if colorId == obj['c'] :
                colorImgs.append(obj['f'])

        if not colorImgs :
            raise Exception('get imgs Fail')

        return colorImgs

    def get_listPrice_old(self,area):
        old_price_text = area('a[href^="javascript:tellAFriend"]').prev().prev().text()
        old_price_tmp = re.search(r'Orig: (.*?) ',old_price_text,re.DOTALL).groups()[0].strip()

        if old_price_tmp :
            unit = old_price_tmp[0]
            listPrice = old_price_tmp[1:]
        else :
            raise ValueError,'Get list price Fail'

        if unit != '$' :
            raise ValueError,'Get unit Fail'

        return 'USD',listPrice

    def get_all_price(self,area):
        priceBlock = area('#Price .productPrice').text().replace('\n','')
        lPriceBlock = (area('#Price .origPrice').text() or priceBlock).replace('\n','')

        if not priceBlock :
            raise Exception('get price Block Fail')

        unit = priceBlock.strip()[0]

        if unit != '$' :
            raise Exception('currecny Error, It\'s {0}'.format(unit))

        currecny = 'USD'

        price = re.search(r'(\d[\d\.]*)',priceBlock).groups()[0]
        listPrice = re.search(r'(\d[\d\.]*)',lPriceBlock).groups()[0]

        if not price or not listPrice :
            raise Exception('get price fail')

        return currecny,price,listPrice



    def get_pdata_old(self,pqhtml):
        productInfo = re.search(r'.*?ga\(\'ec:addProduct\', (\{.*?\})\);',pqhtml('script').text(),re.DOTALL)

        if productInfo :
            return json.loads(productInfo.groups()[0].replace('\'','"'))

        raise ValueError,'get productInfo fault'

    #2016-12-15日添加
    def get_pdata(self,pqhtml):
        info = None
        for ele in pqhtml('script').items() :
            if 'sf.productDetail.init' in ele.text():
                info = re.search(r'sf\.productDetail\.init\((.*)\);\s*\}\);',ele.text(),re.DOTALL).groups()[0]
                break
        else :
            raise Exception('get pdata Fail')

        if not info :
            raise Exception('get pdata info Fail')

        info = demjson.decode(info)

        # print json.dumps(info)

        return info

   
