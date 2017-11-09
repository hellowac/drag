#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/07"

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
            area = pqhtml('.noBorders')
            sdata = self.get_sdata(pqhtml)
            domain = tool.get_domain(url)

            #下架
            if not area :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            # print area.outerHtml()
            # exit()

            detail = dict()

            #图片
            img,imgs = self.get_imgs(area)
            detail['img'] = img
            detail['imgs'] = imgs

            #名称
            detail['name'] = 'Mango ' + area('div[itemprop="name"]').text()

            #品牌
            detail['brand'] = 'Mango'

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #价格符号
            currency = sdata['country']['currencyCode']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品id
            productId = re.search(r'(\d+)',area('.referenciaProducto').text()).groups()[0]
            detail['productId'] = productId

            #颜色
            color = self.get_color(area)
            detail['color'] = color
            detail['colorId'] = dict([(key,key) for key in color.keys()])

            #钥匙
            detail['keys'] = color.keys()

            #规格
            sizes = self.get_sizes(area)
            detail['sizes'] = sizes

            #描述
            detail['descr'] = area('#accordion_ficha').text()

            #详细
            detail['detail'] = area('#collapseTwo').text()

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


    def get_sizes(self,area):
        elements = area('input.inputOcultoColor')

        sizes = dict()
        for ele in elements.items() :
            colorId = ele.prev()('img').attr('data-quick')
            sizeArr = map(lambda x : x.split('|'),ele.attr('value').split('#'))

            #[sizeID,库存标识,显示名称,显示标记]
            sizeObj = []
            for size in sizeArr :
                sizeName = size[2]
                #该size没有库存
                if '-' in sizeName :
                    sizeName = sizeName.split('-')[0].strip()
                    inv = 0
                else :
                    inv = self.cfg.DEFAULT_STOCK_NUMBER

                obj = dict(name=sizeName.strip(),inventory=inv,sku=size[0])

                sizeObj.append(obj)

            sizes[colorId] = sizeObj

        return sizes



    def get_color(self,area):
        elements = area('.productColors__buttonContainer')

        color = dict()
        for ele in elements.items() :
            colorId = ele('img').attr('data-quick')
            colorName = ele('img').attr('title').strip()

            if '-' in colorName :
                colorName = colorName.split('-')[0].strip()

            color[colorId] = colorName

        return color 


    def get_all_price(self,area):
            
        priceBlock = area('span[itemprop="price"]')
        
        #listPrice
        ptxt = priceBlock.text().replace(',','')

        ptxt = re.sub(r'\.\s*','.',ptxt)

        listPrice = re.search(r'(\d[\d\.]+)',ptxt).groups()[0]

        #price
        ptxt = area('.ficha_precio_venta_entero').text() + area('.ficha_precio_venta_decimal').text()
        if not ptxt :
            ptxt = priceBlock.text()

        price = re.search(r'(\d[\d\.]+)',ptxt.replace(',','')).groups()[0]

        return price,listPrice


    def get_imgs(self,area):
        elemtns = area('.imagenes-contenedor div[name="detalles"]')

        imgs = dict()
        img = dict()
        for ele in elemtns.items() :
            colorId = ele.attr('id').split('_')[-1]
            imgArr = [ item.attr('data-src') for item in ele('table img').items() ]
            imgArr = filter(lambda x : x , imgArr)
            imgArr = map(lambda x : x.replace('/S1/','/S20/'),imgArr)

            imgs[colorId] = imgArr
            img[colorId] = imgArr[0]



        return img,imgs

    def get_sdata(self,pqhtml):
        Jtxt = pqhtml('head script[type="text/javascript"]').text()
        data = re.search(r'shopJson = (.*?);\s*var',Jtxt,re.DOTALL).groups()[0]

        return json.loads(data)


    def get_multi_data(self,Jtxt):
        link_data = re.search(r'viewObjectsJson = (.*?);\s*var',Jtxt,re.DOTALL).groups()[0]
        params = json.loads(link_data)['catalogParameters']

        #官网接口
        one = 'http://www.mangooutlet.com/services/productlist/products/' + '/'.join([params['isoCode'],params['idShop'],params['idSection']])

        option = params['optionalParams']

        tmpArr = []
        for k,v in option.items() :
            if isinstance(v,basestring) :
                tmpArr.append(k+'='+v)
            elif isinstance(v,list) :
                tmpArr.append(k+'='+v[0])

        # print map(lambda x: x[0]+'='+x[1],option.items())

        two = '&'.join(tmpArr)

        three = '&pageNum=1&rowsPerPage=20'

        link = one + '?' + two + three

        resp = self.session.get(link, verify=False)

        data = json.loads(resp.text)

        return data['groups'][0]['garments']


    

