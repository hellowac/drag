#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/27"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
from requests.exceptions import TooManyRedirects
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

            area = pqhtml('#content')

            self.link_area = re.search(r'/en-(\w{2})/',url).groups()[0]

            SoldOut = self.checkSoldOut(pqhtml)

            if SoldOut :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)


            pdata = self.get_pdata(area)

            detail = dict()

            #品牌
            brand = pdata['brand']['name']
            detail['brand'] = brand

            #名称
            detail['name'] = brand+' '+pdata['name']

            #货币单位
            currency = pdata['price']['currency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(pdata)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #图片集
            imgsTmp = self.get_imgs(area)
            detail['img'] = imgsTmp[0]
            detail['imgs'] = imgsTmp

            #规格
            sizesTmp = self.get_sizes(pdata)

            if sizesTmp is None :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)
            
            #处理one size
            if len(sizesTmp) == 1 and sizesTmp[0]['name'].lower() in ['one size','onesize'] :
                sizesTmp[0]['name'] = self.cfg.DEFAULT_ONE_SIZE

            detail['sizes'] = sizesTmp

            #视频
            if 'videos' in pdata and pdata['videos'] :
                detail['video'] = self.get_video(pdata)

            #产品注意:
            detail['note'] = area('section.product-accordion--desktop>section:first').text()

            #产品sizeFit
            detail['sizeFit'] = area('section.product-accordion--desktop>section:eq(1)').text()

            #产品详情
            detail['detail'] = area('section.product-accordion--desktop>section:eq(2)').text()
            
            #产品送货
            detail['delivery'] = area('section.product-accordion--desktop>section:last').text()

            #产品退货
            detail['returns'] = area('section.product-accordion--desktop>section:last').text()

            #描述
            detail['descr'] = self.get_descr(area)

            #产品ID
            detail['productId'] = pdata['id']

            print 

            #颜色
            detail['color'] = pdata['colourInfo'][0]['colourName'] if pdata['colourInfo'] else self.cfg.DEFAULT_ONE_COLOR

            #颜色ID
            detail['colorId'] = (pdata['colourInfo'][0]['colourId'] or self.cfg.DEFAULT_COLOR_SKU) if pdata['colourInfo'] else pdata['id']

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

        except TooManyRedirects as e :
            self.logger.exception(e)

            data = tool.get_off_shelf(code=0,message=self.cfg.SOLD_OUT,backUrl=url, html=str(e))
            
            return tool.return_data(successful=False, data=data)

        except Exception, e:
            raise


    def checkSoldOut(self,pqhtml):
        try:
            soldOut = pqhtml('#main .pl-soldout')
            if soldOut :
                return True

            return False

        except Exception, e:
            raise


    def get_video(self,jdata):
        url = jdata['videos']['urlTemplate']
        vtype = jdata['videos']['mediaType']
        types = jdata['videos']['types']

        vlink = url.replace('{{scheme}}','http:').replace('{{type}}',types[0])

        return [ dict(type=vtype,link=vlink) ]


    def get_descr(self,area):
        try:
            sections = area('.product-accordion--desktop:first')
            descr = ''
            if sections :
                for section in sections.items() :
                    descr += (sections.text()+' ')

                return descr

            raise ValueError,'Get Descr Fail'
        except Exception, e:
            e.message += ('function : get_descr')
            raise 


    def get_sizes_old(self,jdata):
        '''
            before 2016-10-14 is old 
        '''
        skus = jdata['skus']

        suburl =  [[str(sku['id']),str(sku['displaySize'])] for sku in skus]

        if len(skus)== 1 and skus[0]['displaySize']== 'n/a' and skus[0]['stockLevel'] == 'In_Stock' :
            return [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=skus[0]['id'],id=skus[0]['id'])]

        elif len(skus)== 1 and skus[0]['displaySize']== 'n/a' :
            return [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=0,sku=skus[0]['id'],id=skus[0]['id'])]

        brand = jdata['brand']['name']

        infos = str(suburl).replace(' ','').replace('\'','')[1:-1]
        cateOne = jdata['categories'][0]['urlKey']
        cateTwo = jdata['categories'][0]['children'][0]['urlKey']
        cateThree = jdata['categories'][0]['children'][0]['children'][0]['urlKey']

        skuinfo = 'http://www.mrporter.com/en-cn/skuinfo/%s/?categoryOne=%s&categoryTwo=%s&categoryThree=%s&designer=%s' %(infos,cateOne,cateTwo,cateThree,brand)

        skusInfoURL=skuinfo

        response = self.session.get(skusInfoURL, verify=False)

        if response.status_code != 200 :
            return None

        def filterSize(obj):
            if 'Sold Out' in obj['name'] :
                obj['name'] = obj['name'].split('-')[0]

        skus = json.loads(response.text)['skus']
        if skus : 
            sizes = [{'name':sku.get('displaySize',sku['size']),'sku':sku['id'],'inventory': sku['stock']} for sku in skus ]

            if sizes :
                map(filterSize,sizes)
                return sizes

        return None

    def get_sizes_old2(self,jdata):
        '''
            before 2016-10-14 is old 

            cn的地区可获取详细库存.
            其他地区不能获取
        '''
        skus = jdata['skus']

        # print json.dumps(jdata)

        if len(skus)== 1 and skus[0]['displaySize'].lower() in ['n/a','one size'] and skus[0]['stockLevel'] == 'In_Stock' :
            return [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=skus[0]['id'],id=skus[0]['id'])]

        elif len(skus)== 1 and skus[0]['displaySize'] in ['n/a','one size'] :
            return [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=0,sku=skus[0]['id'],id=skus[0]['id'])]

        #此分支已舍弃
        # if self.link_area in ['cn','hk'] :
        try:
            skus = jdata['skus']

            suburl =  [[str(sku['id']),str(sku['displaySize'])] for sku in skus]

            scheme = 'US' if 'US' in suburl[0][1] else 'EU' if 'EU' in suburl[0][1] else 'UK' if 'UK' in suburl[0][1] else '*'

            brand = jdata['brand']['name']

            infos = str(suburl).replace(' ','').replace('\'','')[1:-1]
            cateOne = jdata['categories'][0]['urlKey']
            cateTwo = jdata['categories'][0]['children'][0]['urlKey']
            cateThree = jdata['categories'][0]['children'][0]['children'][0]['urlKey']

            skuinfo = 'https://www.mrporter.com/en-{location}'\
                    '/skuinfo/{info}/?categoryOne={cone}'\
                    '&categoryTwo={ctwo}&categoryThree={cthree}'\
                    '&regionSizeScheme={sizescheme}&designer={designer}'.format(
                        location=self.link_area,
                        info=infos,
                        cone=cateOne,
                        ctwo=cateTwo,
                        cthree=cateThree,
                        sizescheme=scheme,
                        designer=brand)

            skusInfoURL=skuinfo

            response = self.session.get(skusInfoURL, verify=False)

            if response.status_code != 200 :
                return None

            def filterSize(obj):
                if 'Sold Out' in obj['name'] :
                    obj['name'] = obj['name'].split('-')[0]

            respdata = json.loads(response.text)

            # print response.text

            skus = respdata['skus']

            print json.dumps(respdata)
            if skus : 
                # sizes = [{'name':sku.get('displaySize',sku['size']),'sku':sku['id'],'inventory': sku['stock']} for sku in skus ]
                sizes = [{'name':sku.get('size',sku['displaySize']),'sku':sku['id'],'inventory': sku['stock']} for sku in skus ]

                if sizes :
                    map(filterSize,sizes)
                    return sizes

            return None
        except Exception as e:
            sizes = list()

            stock=dict(
                Low_Stock = 1,
                In_Stock=self.cfg.DEFAULT_STOCK_NUMBER,
                Out_of_Stock=0,
            )
            for sku in skus :
                inv = stock[sku['stockLevel']]

                obj = dict(name=sku.get('size',sku.get('displaySize',sku['displaySizeLabel']),sku['']),id=sku['id'],sku=sku['id'],inventory=inv)

                sizes.append(obj)

            if not sizes :
                raise ValueError('get sizes fail.')

            return sizes

    def get_sizes(self,jdata):
        
        skus = jdata['skus']

        # print json.dumps(jdata)

        if len(skus)== 1 and skus[0]['displaySize'].lower() in ['n/a','one size'] and skus[0]['stockLevel'] == 'In_Stock' :
            sizes = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=skus[0]['id'],id=skus[0]['id'])]

        elif len(skus)== 1 and skus[0]['displaySize'] in ['n/a','one size'] :
            sizes = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=0,sku=skus[0]['id'],id=skus[0]['id'])]
        else :
            sizes = []
            for sku in skus :
                stockLevel = sku['stockLevel']
                inv = self.cfg.DEFAULT_STOCK_NUMBER if stockLevel.lower() == 'in_stock' else 1 if stockLevel.lower() == 'low_stock' else 0
    
                sid = sku['id']
    
                if stockLevel.lower() == 'out_of_stock' :
                    sid = sid.replace('-so','') 
    
                obj = dict(
                    # name = sku.get('displaySize',sku['displaySizeLabel']),
                    name = sku.get('displaySize'),
                    inventory = inv,
                    id= sid,
                    sku=sid,
                )
    
                sizes.append(obj)

        return sizes


    
    def get_imgs(self,area):
        try:
            lis = area('ul.bxslider:first>li img')
            imgs = []

            if lis :
                for li in lis.items():
                    imgs.append('http' + ':' + li.attr('data-src').replace('xs.','xl.'))

                return imgs

            raise ValueError,'Get imgs Fail'

        except Exception, e:
            e.message += ('function : get_imgs')
            raise 


    def get_all_price(self,jdata):
        try:
            data = jdata['price']
            if data :
                divisor = data['divisor']
                price = round(float(data['amount'])/divisor,2)

                try:

                    listPrice = round(float(data['originalAmount'])/divisor,2)

                except KeyError:

                    listPrice = price
            
            return price,listPrice

        except Exception, e:
            e.message += ('function : get_all_price')
            raise 


    #获取产品数据
    def get_pdata(self,area):
        try:
            jsonData = area('script#productData').text()
            if jsonData :
                return json.loads(jsonData)

            raise ValueError,'Get pdata Fail'

        except Exception, e:
            e.message += ('function : get_pdata')
            raise 

