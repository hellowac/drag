#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/25"

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
            area = pqhtml('.product-essential')
            pdata = self.get_pdata(area)

            # print json.dumps(pdata)
            
            # print area.outerHtml()
            # exit()

            #下架
            if (pdata and not pdata['disable_out_of_stock_option'] ) or ('In stock' not in area('.availability').text()):

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = 'Brooks England'
            detail['brand'] = brand

            #货币
            currency = re.search(r'var dlCurrencyCode = \'(\w{3})\';',pqhtml('script').text()).groups()[0]
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #可以获取到配置
            if pdata :
                #名称
                detail['name'] = brand + ' ' +pdata['productName']

                #价格
                price,listPrice = pdata['basePrice'],pdata['oldPrice']
                detail['price'] = price
                detail['listPrice'] = listPrice

                #颜色
                color,colorId,img,sizes = self.get_info(pdata)
                detail['color'] = color
                detail['colorId'] = colorId

                #钥匙
                if isinstance(color,dict) :
                    detail['keys'] = color.keys()

                #图片集
                imgs = self.get_imgs(area,color)
                detail['img'] = img
                detail['imgs'] = imgs

                #产品ID
                productId = pdata['productId']
                detail['productId'] = productId

                #规格
                detail['sizes'] = sizes

                #描述
                detail['descr'] = pdata['description'] + pqhtml('.technical-info .technical-info-box').text()

            #获取不到配置
            else :
                detail['name'] = brand+' '+area('.product-name:first').text()
                detail['descr'] = area('.description-content').text()

                price,listPrice = self.get_all_price(area('.product-shop'))
                detail['price'] = price
                detail['listPrice'] = listPrice

                productId= area('input[name="product"]').attr('value')

                imgs = self.get_imgs(area,'')
                detail['img'] = imgs[0]
                detail['imgs'] = imgs

                detail['productId'] = productId
                detail['colorId'] = productId
                detail['color'] = self.cfg.DEFAULT_ONE_COLOR
                detail['sizes'] = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=productId,id=productId)]

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


    def get_all_price(self,priceBox):
        try:
            box = priceBox('.price-box')

            symbol = box('span.symbol').text()

            if symbol != u'€' :
                raise ValueError('price symbol isn\'t € ')

            box.remove('.symbol')

            price = box('.price').text().replace(',','').strip()

            listPrice = box('.oldprice').text() or price

            return price,listPrice

        except Exception, e:

            raise


    def get_imgs(self,area,color):
        try:
            
            for ele in area('script').items() :
                if 'configurableGallery' in ele.text() :
                    dtxt = ele.text()
                    break
            else :
                raise ValueError('get Img data Fail , fix this bug')

            dtxt=dtxt.replace('var ','')
            dtxt=dtxt.replace('.push','.append')

            exec dtxt

            #多颜色,One size
            if isinstance(color,dict) :
                imgs = {}
                for cId,colorName in color.items() :
                    imgs[cId] = list(set(configurableGallery[colorName.lower()]))

            #多size， One Color
            elif isinstance(color,basestring) :
                imgs = configurableGallery.values()[0]

            return imgs


        except Exception, e:
            raise


    def get_info(self,pdata):
        try:
            
            if len(pdata['attributes']) > 1 :
                raise ValueError('product attributes great than 1 , fix this bug')

            invAttr = pdata['stockInfo']

            #衣服类,多size但 one color
            if pdata['attributes'].values()[0]['code'] == 'clothing_size' :
                color = self.cfg.DEFAULT_ONE_COLOR
                img = pdata['childProducts'].values()[0]['imageUrl']
                sizes = [ dict(sku=attr['products'][0],id=attr['id'],name=attr['label'],inventory=invAttr[attr['products'][0]]['stockQty'] if invAttr[attr['products'][0]] else 0 ) for attr in pdata['attributes'].values()[0]['options'] ]
                colorId = pdata['attributes'].values()[0]['id']

            #多颜色但one size 一类.
            elif pdata['attributes'].values()[0]['code'] == 'color' :
                color = dict([ (attr['products'][0],attr['label']) for attr in pdata['attributes'].values()[0]['options'] ])
                img = dict([(cId,item['imageUrl']) for cId,item in pdata['childProducts'].items() ])
                sizes = {cId:[dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=invAttr[cId]['stockQty'] if invAttr[cId]['is_in_stock'] else 0 ,sku=cId,id=cId)] for cId,attr in pdata['childProducts'].items() }
                colorId = dict([(key,key) for key in color.keys()])

            return color,colorId,img,sizes


        except Exception, e:
            raise


    def get_pdata(self,area):
        try:

            g = re.search(r'new Product.Config\((.*)\);',area('script').text())

            if not g :
                print('Warning : Get product config fail , check it isn\'t One Color One Size ?')
                return None

            return json.loads(g.groups()[0])

        except Exception, e:
            raise

