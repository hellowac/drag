#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/29"

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

            #前期准备
            Jtxt = pqhtml('script').text()
            area = pqhtml('div.body-wrap>div#page-container section.product-area')
            varea = pqhtml('div.body-wrap>div#page-container section.product-large-view-container')
            self.imgPrefix = re.search(r"productImagePrefix:\s*'(.*?)'",Jtxt,re.DOTALL).groups()[0]

            # print area.outerHtml().encode('utf-8')
            # exit()

            #下架
            if resp.url[resp.url.rfind('/'):] != url[url.rfind('/'):] or pqhtml('.cat-button').hasClass('soldout') :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)
            
            detail = dict()

            #名称
            detail['name'] = area('h1.product-title').text()

            #品牌
            detail['brand'] = self.get_brand(area)

            #货币
            currency = area('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #描述
            detail['descr'] = area('div.product-info').text() + area('div.product-more-details').text()

            #产品ID
            productId = area('.buying-area input.buy').attr('value') or area('.buynow').attr('href').split('buy=')[-1]
            detail['productId'] = productId

            #退货
            detail['returns'] = area('div.product-delivery-returns').text()

            #图片集
            imgsTmp = self.get_imgs(varea)

            #颜色
            color = self.get_color(area)

            detail['color'] = color

            #钥匙
            if isinstance(color,dict) :
                detail['keys'] = color.keys() 
                detail['colorId'] = dict([ (Id,Id) for Id in color.keys() ])
            else :
                detail['colorId'] = productId

            #信息.图片,价格
            sizes,imgs,price,listPrice = self.get_info(area,varea,url)

            #价格
            detail['img'] = imgs[0] if isinstance(imgs,list) else dict( [ (cid,arr[0]) for cid,arr in imgs.items() ])
            detail['imgs'] = imgs
            detail['sizes'] = sizes
            detail['price'] = price
            detail['listPrice'] = listPrice


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


    def get_info(self,area,varea,url):
        formElements = area('div.variation-dropdowns form')

        domain = tool.get_domain(url)

        productId = re.search(r'/(\d*).html',url,re.DOTALL).groups()[0]

        colorValues = None 

        for form in formElements.items() :
            if form('legend').text().find('Colour') != -1 :
                colorValues = [opt.attr('value') for opt in form('select>option').items() if opt.attr('value')]
                break
        else :
            sizes = [{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':self.cfg.DEFAULT_STOCK_NUMBER,'sku':self.cfg.DEFAULT_SIZE_SKU,'id':self.cfg.DEFAULT_SIZE_SKU}]
            imgs  = None
            prices = None
            oldPrices = None

        price = None
        listPrice =None
        imgs = None
        if colorValues :

            for form in formElements.items() :
                if form('legend').text().find('Size') != -1 :
                    sizeValues = [opt.attr('value') for opt in form('select>option').items() if opt.attr('value')]
                    break
            else :
                raise ValueError,'Get size Values Fail'

            sizes = {}
            imgs = {}
            price = {}
            listPrice = {}

            #variation1 代表size ,variation2 代表colour,
            data = {'selected':2,'variation2':2,'variation1':1}
            url = domain + '/variations.json?productId={productId}'.format(productId=productId)
            for cv in colorValues :
                data['option2'] = cv
                sizes[cv] = []


                for sv in sizeValues :
                    data['option1'] = sv

                    resp = self.session.post(url,data=data)
                    jdata = json.loads(resp.text)

                    size = self.get_sizes_by_json(jdata)

                    sizes[cv].append(size)

                    imgs[cv] = self.get_imgs_by_json(jdata)
                    price[cv] = jdata['price'].split(';')[1]
                    listPrice[cv] = jdata['rrp']

        #单颜色价格
        if not price or not listPrice :
            price,listPrice = self.get_all_price(area)

        if not imgs :
            imgs = self.get_imgs(varea)

        return sizes,imgs,price,listPrice

    def get_sizes_by_json(self,jdata):

        price = re.search(r'(\d[\d\.]*)',PyQuery(jdata['price']).text()).groups()[0]
        oldPrice = str(jdata['rrp'])
        
        for variation in jdata['variations'] :
            if variation['variation'] == 'Size' :
                opt = variation['options'][0]
                size = dict(name=opt['name'],id=opt['id'],inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=opt['id'],price=price,listPrice=oldPrice)
                break
        else :
            size = dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=self.cfg.DEFAULT_SIZE_SKU,id=self.cfg.DEFAULT_SIZE_SKU)

        return size

    def get_imgs_by_json(self,jdata):
        imgArr = jdata['images']

        imgs = dict([(img['index'],img['name']) for img in imgArr if img['type'] == 'extralarge'])

        imgs = map(lambda x: self.imgPrefix+x[1],sorted(imgs.iteritems(), reverse=False ))      #排序,保证和官网一致.

        return imgs

    def get_color(self,area):
        
        formElements = area('div.variation-dropdowns form')

        for form in formElements.items() :
            if form('legend').text().find('Colour') != -1 :
                color = dict([(opt.attr('value'),opt.text()) for opt in form('select>option').items() if opt.attr('value') ])
                break
        else :
            trElements = area('div.product-more-details table tr')

            if len(trElements) > 0 :
                for tr in trElements.items() :
                    if 'colour' in tr('th').text().lower() :
                        color = tr('td').text()
                        break
                else :
                    color = self.cfg.DEFAULT_ONE_COLOR
            else :
                raise ValueError,'Get Color Fail'

        return color


    def get_imgs(self,varea):
        imgs = [ imgA.attr('href') for imgA in varea('ul.product-thumbnails>li>a').items()]
        
        return imgs


    def get_all_price(self,area):
        ptxt = area('span.price').text().replace(',','')

        price = re.search(r'(\d[\d\.]*)',ptxt,re.DOTALL).groups()[0]


        ptxt = area('span.price').text().replace(',','')
        ptxt1 = area('p.yousave').text().replace(',','')

        listPrice = float(price)

        if ptxt :
            ptxt = re.search(r'(\d[\d\.]*)',ptxt,re.DOTALL).groups()[0]

            listPrice += float(ptxt)

        elif ptxt1 :
            ptxt1 = re.search(r'(\d[\d\.]*)',ptxt1,re.DOTALL).groups()[0]
            
            listPrice += float(ptxt1)
            
        return price,str(listPrice)



    def get_brand(self,area):
        trElements = area('div.product-more-details table tr')

        if len(trElements) > 0 :
            for tr in trElements.items() :
                if 'brand' in tr('th').text().lower() :
                    brand = tr('td').text()
                    break
            else :
                brand = 'THEHUT'

        return brand




    

