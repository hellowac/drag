#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/21"

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
            
            resp = self.session.get(url, verify=False)                #加载第一次.

            #验证resp.防爬虫.!!!
            resp = self.resp_verify(resp)             

            if 'window.location.reload(true);' in resp.text :

                resp = self.session.get(url, verify=False)            #加载第二次.

            #会出现不返回内容的情况
            while not resp.text :
                return self.detail(url, verify=False)

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

            #下架
            if 'Out of stock' in pqhtml('.product-availability').text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            #前期准备
            area = pqhtml('div#product-view')
            domain = tool.get_domain(url)
            pdata = self.get_pdata(area)

            detail = dict()

            #品牌
            brand = area('.panel-a h1:first').text().split('-')[0].strip()
            detail['brand'] = brand

            #名称
            detail['name'] = area('.panel-a h1:first').text()

            #货币
            currency = pqhtml('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品ID
            productId = pdata['productId']
            detail['productId'] = productId

            #价格
            price,listPrice = pdata['basePrice'].replace(',',''),pdata['oldPrice'].replace(',','')
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            # color = self.get_color(area)
            detail['color'] = area('button#product-addtocart-button').attr('data-variant') or self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = productId

            #图片集
            imgs = [ img.attr('data-src') for img in area('div#mobile-carousel-images a>img').items()]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = self.get_sizes(area,pdata)

            #描述
            detail['descr'] = area('div.tog-desc').text() + area.parent()('.description-section:first').text()

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


    def get_sizes(self,area,pdata):
        try:

            invBlock = area('.availability-only').text()

            if invBlock and 'Only' in invBlock :
                inv = re.search(r'Only (\d) left',invBlock).groups()[0]
            else :
                inv = self.cfg.DEFAULT_STOCK_NUMBER

            sizes = {}
            for Id,attribute in pdata['attributes'].items():
                if attribute['label'] == 'Size' :
                    sizes = [{'name':opt['label'],'inventory':inv,'id':opt['id'],'sku':opt['id']} for opt in attribute['options']]
                    break

            else :
                sizes = [{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':inv,'id':self.cfg.DEFAULT_SIZE_SKU,'sku':self.cfg.DEFAULT_SIZE_SKU}]
            
            return sizes

        except Exception, e:
            raise


    def get_pdata(self,area):
        try:
            conf = re.search(r'new Product.Config\((.*?\}\})\);',area.text())

            if not conf : 
                raise ValueError,'Get productConf Fail'

            return json.loads(conf.groups()[0])

        except Exception, e:
            raise


    def resp_verify(self,resp):
        try:
            
            if resp.status_code != 200 :
                raise ValueError,'server status : {status}, text:{text}'.format(status=resp.status_code,text=resp.text)

            elif 'var b' in resp.text :
                resp = self.verify(resp)

                #最大尝试深度
                depIndex = 50 

                while 'var b=' in resp.text and depIndex:
                    resp = self.verify(resp)
                    depIndex -= 1
                    # print 'veirfy retrie number :',depIndex

                #尝试到最大深度
                if depIndex == 0 :
                    raise ValueError,'kicksusa verify depIndex max retrie error'

                #没有认定我为robots.
                if 'NAME="ROBOTS"' not in resp.text :
                    return resp

                #验证其他情况
                raise ValueError,'kicksusa verify new condition'

            elif 'Request unsuccessful' in resp.text : 
                raise ValueError,'Request unsuccessful sever need to Img verify'

            return resp

        except Exception, e:
            raise


    def verify(self,resp):
        try:
            
            if 'var b' in resp.text :

                varB = re.search(r';var b="([\d\w]*)";',resp.text,re.DOTALL)
                if varB :
                    varB = varB.groups()[0]

                    z = ''
                    for i in range(0,len(varB)-1,2) :
                        z += chr(int(varB[i:i+2],16))

                    url = re.search(r'xhr\.open\("GET","(.*?)",false\)',z)

                    if url :
                        url = 'http://www.kicksusa.com' + url.groups()[0]

                        resp = self.session.get(url, verify=False)

                        if resp.status_code != 200 :

                            raise 'kicksusa verify fail.'

                        else :
                            return resp
                    else :
                        raise ValueError,'verify convert z Fault'
                else :
                    raise ValueError,'verify search varB fault'
            else :
                raise ValueError,'var b not in resp.text'

        except Exception, e:
            raise

   

