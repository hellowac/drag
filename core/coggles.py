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
            domain = tool.get_domain(url)

            #下架:
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
            Jtxt = pqhtml('script').text()
            area = pqhtml('.product-area')

            dataLayer = json.loads(re.search(r'dataLayer = \[(\{.*?\})\];',Jtxt,re.DOTALL).groups()[0].replace('\'','"'))

            #默认官网只有一个颜色,一个产品,多颜色多size，多colorID已处理好，但是多颜色多图片没有处理. 在 get_imgs 方法.
            assert len(dataLayer['productDetails']) == 1 ,'coggles too many products , fix this bug'

            instock = area('meta[itemprop="availability"]').attr('content') == 'InStock'

            #下架
            if not instock or dataLayer['productDetails'][0]['productStatus'] != 'Available':

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            productId,pdata = self.get_pdata(domain,dataLayer)

            # print area.outerHtml()
            # exit()

            detail = dict()

            #图片
            imgsTmp = self.get_imgs(pdata,pqhtml)
            detail['img'] = imgsTmp[0]
            detail['imgs'] = imgsTmp

            #名称
            detail['name'] = area('.product-title-wrap').text()

            #品牌
            detail['brand'] = re.search(r'productBrand: "(.*?)",',Jtxt,re.DOTALL).groups()[0]

            #价格
            price,listPrice = self.get_all_price(area,pdata)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #价格符号
            currency = dataLayer['pageAttributes'][0]['currency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品id
            prodId = pqhtml('input[name="prodId"]').attr('value')
            detail['productId'] = prodId

            #颜色
            color = self.get_color(pdata)
            detail['color'] = color
            detail['colorId'] = dict([(key,key) for key in color.keys()])

            #钥匙
            detail['keys'] = color.keys()

            #规格
            detail['sizes'] = self.get_sizes(productId,pdata)

            #描述
            detail['descr'] = area('div[itemprop="product-description"]').text().replace('\'','') + area('div[itemprop="description"]').text().replace('\'','')

            #注意:
            if len(area('.promotionalmessage')) > 1 :
                detail['note'] = area('.promotionalmessage').text()

            #详细
            detail['detail'] = area('.js-prodInfo-details').text()

            #退货和配送信息
            detail['returns'] = area('div.product-delivery-returns').text().replace('\'','')

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
        try:

            if pdata :
                #---------------------目前发现官网都是一个颜色....有2种以上颜色请告知.

                colors = [ variation['options'] for variation in pdata['variations'] if variation['variation'] == 'Colour']

                color = dict([ (color['id'],color['name']) for color in colors[0] ])

            else :
                color = {self.cfg.DEFAULT_COLOR_SKU:self.cfg.DEFAULT_ONE_COLOR}

            return color

        except Exception, e:
            raise


    def get_sizes(self,productId,pdata):
        try:
            inventory = self.cfg.DEFAULT_STOCK_NUMBER

            if pdata :
                colour = [ variation for variation in pdata['variations'] if variation['variation'] == 'Colour' ][0] if len(pdata['variations']) > 1 else None
                sizes_ = [ variation for variation in pdata['variations'] if variation['variation'] == 'Size' ][0] if len(pdata['variations']) > 1 else None

                sizes = {}
                link = 'http://www.coggles.com/variations.json?productId={pid}'.format(pid=productId)

                data = dict(selected=2,variation1=1,variation2=2)
                if colour and sizes_ :
                    for color in colour['options'] :

                        data.update(option2=color['id'])

                        sizes[color['id']] = []

                        for size in sizes_['options'] :

                            data.update(option1=size['id'])

                            info = json.loads(self.session.post(link,data).text)

                            price = re.search(r'(\d+[\.\d]*)',PyQuery(info['price']).text()).groups()[0]

                            obj = dict(name=size['name'],inventory=inventory,id=size['value'],sku=size['id'],price=price,oldPrice=info['rrp'])

                            sizes[color['id']].append(obj)
                            
                    if len(sizes.keys()) > 1 :
                        raise ValueError,u'coggles find many color ,fix this bug'

                    sizes = sizes

                else :

                    sizes = [{ 'name':size['name'],'inventory':inventory,'sku':size['id'],'id':size['value']} for variation in pdata['variations'] if variation['variation'] == 'Size' for size in variation['options']]

            elif 'productDetails' in pdata and pdata['productDetails'][0]['productStatus'] != 'Available':

                sizes = [{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':0,'sku':self.cfg.DEFAULT_SIZE_SKU,'id':self.cfg.DEFAULT_SIZE_SKU}]

            else :

                sizes = [{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':inventory,'sku':self.cfg.DEFAULT_SIZE_SKU,'id':self.cfg.DEFAULT_SIZE_SKU}]
                
            return sizes

        except Exception, e:
            raise e


    def get_imgs(self,pdata,pqhtml):
        try:

            arr = pqhtml('meta[property="og:image"]').attr('content').split('/')

            imgDomain = arr[0]+'//'+arr[2]+'/'

            if pdata :
                imgs = [ imgDomain+img['name'] for img in pdata['images'] if img['type'] == 'zoom']
            else:
                imgs = [ imgA.attr('href') for imgA in pqhtml('ul.product-large-view-thumbs li a').items()]

            return imgs

        except Exception, e:
            raise


    def get_all_price(self,area,pdata):
        # print area.outerHtml()

        if pdata :
            ptxt = pdata['price'].replace(',','')
            price = re.search(r'(\d[\.\d]*)',PyQuery(ptxt).text(),re.DOTALL).groups()[0]

            ptxt = pdata['rrpDisplay'] if 'rrpDisplay' in pdata else pdata['price']
            listPrice = re.search(r'(\d[\.\d]*)',PyQuery(ptxt).text(),re.DOTALL).groups()[0]

        else :
            ptxt = area('.product-details p.product-price span.price').text()

            price = re.search(r'(\d[\.\d]*)',ptxt,re.DOTALL).groups()[0]

            listPrice = price

        return price,listPrice

    def get_pdata(self,domain,jdata):
        Id = jdata['productDetails'][0]['productSKU']

        # http://www.coggles.com/variations.json?productId=11268778

        url = domain + '/variations.json?productId={id}'.format(id=Id)
        while 1:
            jdata = json.loads(self.session.get(url, verify=False).text)
            if jdata.has_key('price') or jdata == {}:
                
                return Id,jdata



