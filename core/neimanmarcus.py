#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/06"

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
import base64
import time


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)


    #获取页面大概信息
    def multi(self, url):
        pass



    #获取详细信息
    def detail(self,url):
        pqhtml = ''
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

            need_refresh_node = pqhtml('meta[http-equiv="refresh"]')
            if len(need_refresh_node) :
                time_limit = need_refresh_node.attr('content').strip().split(';')[0]

                sleep_seconds = int(time_limit)/2
                time.sleep(sleep_seconds)

                #<RequestsCookieJar[]>
                self.session.cookies.set('INSTART_SESSION_ID',str(int((time.time()-sleep_seconds)*1000)))

                resp = self.session.get(url, verify=False)

                pqhtml = PyQuery(resp.text)

                area = pqhtml('form[name="productPage"]')

            # print pqhtml.outerHtml()
            #前期准备
            area = pqhtml('div.hero-zoom-frame:first')
            domain = tool.get_domain(url)
            pdata = self.get_pdata(pqhtml,domain)

            #下架
            if 'sold out' in area('.oos_msg').text().lower() or 'sold out' in area('.flag-sold-out').text().lower() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #名称
            detail['name'] = area('h1.product-name').text()

            #品牌
            detail['brand'] = area('a.product-designer').text()

            #颜色
            saleStatus,saleDate,color,sizes = self.get_sizes_color(pdata)
            detail['color'] = color
            detail['colorId'] = dict([(key,key) for key in color.keys()])

            #钥匙
            detail['keys'] = color.keys()

            #图片集
            imgs = self.get_imgs(area)
            detail['img'] = imgs[0] if isinstance(imgs,list) else dict([ (cid,Arr) for cid,Arr in imgs.items() ])
            detail['imgs'] = imgs

            #货币
            currency = pqhtml('#confPdpCurrency').attr('value').strip()
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品ID
            productId = area('input.cmos_item').attr('value')
            detail['productId'] = productId

            #规格
            detail['sizes'] = sizes

            #描述
            detail['descr'] = area('div[itemprop="description"]').text()

            #品牌描述
            detail['brandDescr'] = area('.cutlineDetails').text()

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = saleStatus

            #预售时间
            if saleDate :
                detail['presellDate'] = saleDate

            #返回链接
            detail['backUrl'] = url
            
            #返回的IP和端口
            detail['ip_port']=':'.join(map( lambda x:str(x),resp.raw._original_response.peer))

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)

            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            self.logger.exception('html:{0}'.format(pqhtml))
            raise


    def get_all_price(self,area):
        price = area('input[name="retail0"]').attr('value')

        priceBlock = area('.price-adornments-elim-suites').text()

        if not priceBlock:
            priceBlock = area('.product-price').text()

        priceBlock = priceBlock.replace(',', '')

        g = re.search(r'(\d[\.\d]*)', priceBlock)

        if not g :
            raise ValueError,'Get list price Fail'

        listPrice = g.groups()[0]

        return price,listPrice


    def get_imgs(self, area):
        if len(area('ul#color-pickers>li')) > 1:
            return self.get_imgs_manyColor(area)
        else:
            return self.get_imgs_oneColor(area)


    def get_imgs_manyColor(self, area):
        imgElements = area('ul#color-pickers:first>li')

        colors = {}
        for li in imgElements.items():
            colorName = li('a').attr('id')
            try:
                colorparam = li.attr('data-sku-img')

                colorparam = re.search(
                    r':"(.*?)"', colorparam, re.DOTALL).groups()[0]
                url = 'http://neimanmarcus.scene7.com/is/image/NeimanMarcus/{param}?&wid=1200&height=1500'.format(
                    param=colorparam)
            except Exception, e:
                colorparam = li.attr('data-color-img-params')
                cmosID = area('#prod-img').attr('cmos-id')
                colorKey = li('img').attr('data-color-key')

                url = 'http://neimanmarcus.scene7.com/is/image/NeimanMarcus?'\
                'src=ir{{NeimanMarcusRender/NM{cmosID}_b_{colorKey}?&obj=base_color&src=NM{cmosID}_{colorKey}&obj=imprint1&decal&src=is{{NeimanMarcus/styleA?&$text1=M&$swatch=thread_017}}&res=100&show&sharp=1&sharpen=1}}&resmode=sharp2&qlt=85,1&wid=1456&height=1570'.format(cmosID=cmosID,colorKey=colorKey)

            colors[colorName] = [url]

            return colors


    def get_imgs_oneColor(self, area):
        imgElements = area('.images>.product-thumbnails ul>li img')

        imgs = None
        if imgElements:
            imgs = [ele.attr('data-zoom-url')
                    for ele in imgElements.items() if ele.attr('data-zoom-url')]

        if not imgs:
            imgs = [area('div.img-wrap img').attr('data-zoom-url')]

        if not imgs:
            raise ValueError, 'get Imgs Fail'

        return imgs


    def get_sizes_color(self,pdata):

        print json.dumps(pdata)

        sizeAndColor = pdata['ProductSizeAndColor'][
            'productSizeAndColorJSON']

        sizeAndColor = json.loads(sizeAndColor)

        # assert (len(sizeAndColor) == 1), 'colors not equal 1'

        saleDate = None
        sizes = {}
        colors = {}
        for product in sizeAndColor:
            productId = product['productId']
            for sku in product['skus']:

                #现货
                if sku['status'] == 'In Stock':
                    saleStatus = self.cfg.STATUS_SALE

                #预售
                elif sku['status'] == 'Pre-Order' :
                    saleStatus = self.cfg.STATUS_PRESELL
                    saleDate = time.mktime(time.strptime(sku['availPlainDate'],"%m/%d/%Y"))  

                #其他    
                else :
                    saleStatus = self.cfg.STATUS_ERROR

                color = sku['color'].split('?')[0]
                size = {'name': sku.get('size', self.cfg.DEFAULT_ONE_SIZE), 'inventory': sku[
                    'stockAvailable'], 'sku': sku['sku']}

                if color in sizes:
                    sizes[color].append(size)
                else:
                    sizes[color] = [size]

                if color not in colors:
                    colors[color] = color

        return saleStatus, saleDate, colors, sizes


    def get_pdata(self,pqhtml,domain):
        link = domain + '/product.service'
        productId = pqhtml('input[name="itemId"]').attr('value')
        products = {"ProductSizeAndColor": {"productIds": productId}}
        products = json.dumps(products)

        timestamp = str(int(time.time()*1000))
        b64Info = '$b64$'+base64.b64encode(products)
        data = {'data': b64Info, 'timestamp': timestamp}

        resp = self.session.post(link, data=data)
        # pdata = json.loads(resp.text.decode(resp.encoding))
        pdata = json.loads(resp.text)
        # pdata = eval(resp.text)

        # print resp.text

        # print resp.status_code
        # print resp.encoding

        # exit()

        # pdata = resp.json()

        return pdata

