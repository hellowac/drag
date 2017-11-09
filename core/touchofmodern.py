#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/10"

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
            pqhtml.remove('style')
            area = pqhtml('#overall_content')
            domain = tool.get_domain(url)
            pdata = self.get_pdata(pqhtml)

            # print pqhtml.outerHtml()
            # print area.outerHtml()

            # print json.dumps(pdata)
            # exit()

            #下架
            # if area('div[itemprop="availability"]').text().strip() != 'Available' :

            #     log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            #     self.logger.info(log_info)

            #     data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
            #     return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = 'TouchOfModern'
            detail['brand'] = brand

            #名称
            detail['name'] = brand + ' ' + pdata['name']

            #货币
            currency = pqhtml('meta[property="og:price:currency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            # listPrice = self.get_all_price(area)
            detail['price'] = pdata['price']

            #颜色
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = pdata['id']

            #图片集
            detail['img'] = area('.big_image_wrapper a').attr('href')
            detail['imgs'] = [ e.attr('href') for e in area('div[class="product-image-container"] a').items() ]

            #产品ID
            productId = pdata['id']
            detail['productId'] = productId

            #规格
            listPrice,sizes = self.get_sizes(area)
            detail['sizes'] = sizes
            detail['listPrice'] = listPrice or pdata['price']

            #视频
            if len(area('.product-video-container')) > 0 :
                detail['video'] = self.get_video(area)

            #描述
            detail['descr'] = area('.product-details-section').text()

            #详细
            detail['detail'] = area('.product-details-section').text()

            #退换货
            detail['returns'] = area('.shipping-details-listt').text()

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


    def get_video(self,area):
        ieles = area('.video-container object')

        videos = [ dict(url=e.attr('data'),type=e.attr('type')) for e in ieles.items()]

        return videos 


    def get_sizes(self,area):
        jtxt = area('#product-content script').text()

        variations = re.search(r'var productVariations = (.*);\n',jtxt).groups()[0]

        variations = json.loads(variations)

        listPrice = ''
        sizes = list()

        for key,item in variations.items() :

            listPrice = item['msrp'][1:] or ''

            obj = dict(sku=key,name=item['title'] or self.cfg.DEFAULT_ONE_SIZE,inventory=item['maxqty'] or 0 , listPrice=item['msrp'][1:].replace(',',''))

            sizes.append(obj)

        return listPrice.replace(',',''),sizes



    def get_pdata(self,pqhtml):
        jeles = pqhtml('script')

        for ele in jeles.items() :
            if 'analytics log event' in ele.text() :
                trackData = re.search(r"analytics\.track\('Viewed Product', (\{.*\}) \);\s*",ele.text(),re.DOTALL).groups()[0]
                break
        else :
            raise ValueError,'Get product data fail'

        return json.loads(trackData)
