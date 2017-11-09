#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/11/01"

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
            area = pqhtml('.product-detail')
            detail_tab = pqhtml('#product-detail-tabs')
            img_tab = pqhtml('div.images')

            domain = tool.get_domain(url)
            pdata = self.get_pdata(pqhtml)

            # print area.outerHtml().encode('utf-8')
            # print json.dumps(pdata)
            # print detail_tab.outerHtml().encode('utf-8')
            # print img_tab.outerHtml().encode('utf-8')
            
            # exit()

            #下架
            if not area or 'out of stock' in area('.out-of-stock').text():

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            video_prefix = 'http://image1.superdry.com/static/images/products/'

            detail = dict()

            detail['stock'] = pdata['product']['stock']     #该商品总库存.

            detail['video'] = video_prefix+pdata['product']['video']

            detail['gender'] = pdata['product']['gender']

            detail['season'] = pdata['product']['season']

            detail['category'] = pdata['product']['category']

            detail['productSku'] = pdata['product']['sku_code']

            detail['size_guide'] = pdata['product']['size_guide']

            detail['subcategory'] = pdata['product']['subcategory']

            detail['productCode'] = pdata['product']['sku_code']

            #产品ID
            productId = pdata['product']['id']
            detail['productId'] = productId
            
            #品牌
            brand = 'SUPERDRY'
            detail['brand'] = brand

            #名称
            detail['name'] = pdata['product']['name']

            #货币
            currency = pdata['product']['currency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            detail['price'] = pdata['product']['unit_sale_price']
            detail['listPrice'] = pdata['product']['unit_price']

            #描述
            detail['descr'] =  pdata['product']['description']

            #详细
            detail['detail'] = detail_tab.text()

            #退换货
            detail['returns'] = detail_tab('tab-page:last').text()

            #颜色
            detail['color'] = pdata['product']['color']
            detail['colorId'] = pdata['product']['color']

            #图片集
            imgs = [ ele.attr('src') for ele in img_tab('.scroller li img').items()]
            imgs = map(lambda x : x.replace('/productthumbs/','/zoom/'), imgs)
            detail['img'] = img_tab('.scroller li img:first').attr('src').replace('/productthumbs/','/zoom/')
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = self.get_sizes(area)

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

    def get_sizes(self,area):
        optionElements = area('select#product_id option[value!="0"]')

        sizes = [
            dict(
                name=opt.text() if opt.text() else self.cfg.DEFAULT_ONE_SIZE ,
                inventory=self.cfg.DEFAULT_STOCK_NUMBER,
                sku=opt.attr('value'),
                id=opt.attr('value'),
            )
            for opt in optionElements.items() ]

        if not sizes :
            raise ValueError('get sizes fail')

        return sizes

    def get_pdata(self,pqhtml):
        data = ''

        for ele in pqhtml('script').items() :
            if 'window.universal_variable =' in ele.text() :

                data = re.search(r'window.universal_variable = (.*)\s*window.addEvent',ele.text()).groups()[0]
                break
        else :
            raise ValueError('get pdate is fail')

        import demjson 

        data = demjson.decode(data)

        if not data :
            raise ValueError('get pdate is fail')

        return data















