#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/08/12"

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
            
            #前期准备
            area = pqhtml('form[name="productPage"]')
            domain = tool.get_domain(url)
            
            # print area.html().encode('utf-8')
            # exit()

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

            #下架
            if not area or len(area('.cannotorder')):
            # if not area :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            productId = area('input[name$="productId"][value!=""]').attr('value')
            pdata = self.get_pdata(area,productId)

            detail = dict()


            #产品ID
            detail['productId'] = productId
            
            #品牌
            brand = area('input.cmDesignerName').attr('value')
            detail['brand'] = brand

            #名称
            detail['name'] =area('h1.product-name:first').text()

            #货币
            currency = pqhtml('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)

            detail['price'] = price
            detail['listPrice'] = listPrice

            #描述
            detail['descr'] = area('div[itemprop="description"]').text()

            #详细
            detail['detail'] = area('.product-details-info').text()

            #颜色
            # color = self.get_color(area)
            # detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            # detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

            #图片集
            img,imgs = self.get_imgs(area)
            detail['img'] = img
            detail['imgs'] = imgs

            #规格
            sizes = self.get_sizes(pdata)
            detail['sizes'] = sizes

            if isinstance(sizes,dict):
                detail['keys'] = sizes.keys()
                detail['color'] = {key:key for key in sizes}
                detail['colorId'] = {key:key for key in sizes}

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
            self.logger.exception('html:{0}'.format(pqhtml))
            raise

    def get_pdata(self,area,productId):
        addr = 'http://www.bergdorfgoodman.com/product.service?instart_disable_injection=true'

        data = dict(
            data='$b64$'+base64.b64encode(json.dumps(dict(ProductSizeAndColor=dict(productIds=productId))).replace(' ','')),     #去掉空格.
            sid='getSizeAndColorData',
            bid='ProductSizeAndColor',
            timestamp=int(time.time()*1000)       #13位.
        )

        resp = self.session.post(addr,data=data)

        respJson = resp.json()

        prodJson = json.loads(respJson['ProductSizeAndColor']['productSizeAndColorJSON'])

        return prodJson

    def get_sizes(self,pdata):
        
        if len(pdata) > 1 :
            raise ValueError('get pdata product legnth {0} than one.'.forma(len(pdata)))

        sizes = dict()
        # print json.dumps(pdata)

        for info in pdata[0]['skus'] :

            cName = info['color'].split('?')[0]

            if 'In Stock' in info['status'] :
                inv = info['stockAvailable']
            else :
                inv = 0

            obj = dict(name=info.get('size',self.cfg.DEFAULT_ONE_SIZE),sku=info['sku'],id=info['sku'],inventory=inv)

            if cName not in sizes :
                sizes[cName] = [obj]
            else :
                sizes[cName].append(obj)

        if not sizes :
            raise ValueError('get sizes fail.')

        return sizes


    def get_imgs(self,area):
        colorBlock = area('ul#color-pickers')

        img = dict()
        imgs = dict()

        if colorBlock :
            imgPrefix = 'http://bergdorfgoodman.scene7.com/is/image/bergdorfgoodman/{0}?&wid=1200&height=1500'      #zoom img.
            for li in colorBlock('li.color-picker').items():
                cName = li.attr('data-color-name')
                code = json.loads(PyQuery(li.attr('data-sku-img')).text())['m*']
                img_ = imgPrefix.format(code)

                img[cName] = img_
                imgs[cName] = [img_]

        else :
            img = area('div#prod-img img[itemprop="image"]:first').attr('data-zoom-url')
            imgs = [ ele.attr('data-zoom-url') for ele in area('div#prod-img img[itemprop="image"]').items() ]

        if not img or not imgs :
            raise ValueError('get img and imgs fail.')

        return img,imgs

    def get_all_price(self,area):
        price = area('input[name="sale0"]').attr['value']
        listPrice = area('input[name="retail0"]').attr['value']

        if 'Original' in area('.price-adornments-elim-suites span').text() :
            listPrice = re.search(r'(\d[\d\.]*)',area('.price-adornments-elim-suites span').text(),re.DOTALL).groups()[0]

        if not price or not listPrice :
            raise ValueError('get price or listPrice fail.')

        return price,listPrice


    

