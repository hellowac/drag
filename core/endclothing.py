#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/24"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
import re
import json
import time
import random


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)        
        # print self.session.get('http://geo.yieldify.com/geolocation.json').text 


    #获取页面大概信息
    def multi(self, url):
        pass


    #获取详细信息
    def detail(self,url):
        try:
            #打印当前IP
            # print self.session.get('http://geo.yieldify.com/geolocation.json').text
            # 0627 写一个插件版

            #绑定域名
            self.domain = tool.get_domain(url)

            resp = self.session.get(url, verify=False)

            #end 特有验证
            resp = self.end_verify(resp,url)

            status_code = resp.status_code
            
            pqhtml = PyQuery(resp.text or 'nothing')

            # not found 错误
            if status_code == 404 or '404 not found' in pqhtml('head title').text().lower() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)


            # 非200 错误
            if status_code != 200 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)


            Jtxt = pqhtml('script').text()

            area = pqhtml('div.product-essential')

            #下架
            if 'Sold out' in area('div.product-buy-box').text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            #线下销售
            if len(area('div.notonline')) > 0 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('NTONLINE','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            # print area.outerHtml().encode('utf-8')
            
            #productConfig
            pcfg = self.get_pcfg(Jtxt)

            detail = dict()

            #价格符号
            currency = pqhtml('meta[property="product:price:currency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price, listPrice = self.get_all_price(pcfg)
            detail['price'] = price
            detail['listPrice'] = listPrice

            # print area.outerHtml().encode('utf-8')

            #品牌
            detail['brand'] = pqhtml('meta[name="WT.z_pbrand"]').attr('content') or area('.product-description span h1').text()

            #名称
            detail['name'] = area('h1[itemprop="name"]').text() or area('.product-description h1').text()

            #图片
            imgs = self.get_imgs(area)
            detail['imgs'] = imgs
            detail['img'] = imgs[0]

            #产品ID
            productId = pcfg['productId']
            detail['productId'] = productId

            #颜色
            detail['color'] = area('div.product-description h3:first').text() or self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = productId

            #退换货
            detail['returns'] = area('#prod-info-tab4').text()

            #规格
            detail['sizes'] = self.get_sizes(pcfg)

            #描述
            detail['descr'] = area('div.product-description-text').text()+area('#prod-info-tab2').text()+area('#fit-description').text()

            #配送
            detail['delivery'] = area('#prod-info-tab2').text()

            #size说明.
            detail['sizeFit'] = area('#fit-description').text()

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


    def get_sizes(self,pcfg):
        try:
            sizes = []
            for Id,attribute in pcfg['attributes'].items():
                if attribute['label'] == 'Size':
                    for opt in attribute['options'] :
                        sid = opt['id']
                        label = opt['label']
                        name = label.split(' - ')[0] if ' - ' in label else label
                        inventory = re.search(r'Only\s*(\d*)\s*left',label).groups()[0] if ' - ' in label else self.cfg.DEFAULT_STOCK_NUMBER

                        sizes.append({'name':name,'inventory':inventory,'sku':sid,'id':sid})
                    break
            else :
                sizes = [{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':self.cfg.DEFAULT_STOCK_NUMBER,'sku':self.DEFAULT_SIZE_SKU,'id':self.cfg.DEFAULT_SIZE_SKU}]

            #根据id排序
            sizes = sorted(sizes,key=lambda x: x['id'])

            return sizes

        except Exception, e:
            raise


    def get_all_price(self,pcfg):
        try:
            price = pcfg['basePrice'].replace(',','')
            listPrice = pcfg['oldPrice'].replace(',','')

            return price,listPrice
        except Exception, e:
            e.message += ('function : endclothing ---> get_all_price')
            raise 


    def get_imgs(self,area):
        try:
            imgs = area('div.product-img-box div.slider-for a')

            return [ img.attr('href') for img in imgs.items()]
        except Exception, e:
            e.message += ('function : endclothing ---> get_imgs')
            raise 


    def get_pcfg(self,Jtxt):
        try:
            g = re.search(r'Product.Config\((.*?\}\})\);',Jtxt,re.DOTALL)

            if g : 
                return json.loads(g.groups()[0])

            raise ValueError,'Get productConf Fail'

        except Exception, e:
            e.message += ('function : endclothing ---> get_pcfg')
            raise 


    #endclothing 特有验证
    def end_verify(self,resp,url):
        try:
            verifyResult =  self.resVerify(resp)

            if verifyResult is True :
                resp = self.session.get(url, verify=False)

            notValid = True
            num = 2 
            maxnum = 50
            while notValid:
                if 'http-equiv="refresh"' in resp.text :
                    # print u'第%s次验证:' % num
                    self.verify(resp)
                    resp = self.session.get(url, verify=False)
                    num += 1 
                else :
                    notValid = False

                if num == maxnum :
                    raise ValueError,'over max retries verify number %s' % maxnum

            # 验证分割线----------------------------------

            return resp

        except Exception, e:
            e.message += ('function : endclothing ---> end_verify')
            raise 

    #endclothing response验证
    def resVerify(self,response):
        try:

            if 'id="distil_ident_block"' in response.text or 'id="error-container"' in response.text :
                return self.verify(response)

            elif 'Request unsuccessful' in response.text : 
                raise ValueError,'Request unsuccessful sever need to Img verify'

            return 'verified'

        except Exception, e:
            e.message += ('function : endclothing ---> resVerify')
            raise 

    #endclothing js验证
    def verify(self, response):
        try:
            pqhtml = PyQuery(response.text)

            if 'Blocked' in pqhtml('title').text() or 'Captcha' in pqhtml('title').text():
                raise Exception('endclothing ---> you are Blocked!!!')

            # print pqhtml.outerHtml().encode('utf-8')

            url = self.domain + pqhtml('head>script:last').attr('src')

            response = self.session.get(url, verify=False)

            sub_url = re.search(r'var _0x174c=\["(.[^"]*)","\\x', response.text).groups()[0]

            url = self.domain + sub_url  # response.headers['X-JU']  # 2017年06月01日11:55:18 修改

            p = {
                "appName": "Netscape",
                "platform": random.choice(["Win32","Win64"]),
                "cookies": 1,
                "syslang": "zh-CN",
                "userlang": "zh-CN",
                "cpu": "",
                "productSub": "20030107",
                "setTimeout": 0,
                "setInterval": 0,
                "plugins": {
                    "0": "WidevineContentDecryptionModule",
                    "1": "ShockwaveFlash",
                    "2": "ChromePDFViewer",
                    "3": "NativeClient",
                    "4": "ChromePDFViewer"
                },
                "mimeTypes": {
                    "0": "WidevineContentDecryptionModuleapplication/x-ppapi-widevine-cdm",
                    "1": "ShockwaveFlashapplication/x-shockwave-flash",
                    "2": "ShockwaveFlashapplication/futuresplash",
                    "3": "application/pdf",
                    "4": "NativeClientExecutableapplication/x-nacl",
                    "5": "PortableNativeClientExecutableapplication/x-pnacl",
                    "6": "PortableDocumentFormatapplication/x-google-chrome-pdf"
                },
                "screen": {
                    "width": 1920,
                    "height": 1080,
                    "colorDepth": 24
                },
                "fonts": {
                    "0": "Calibri",
                    "1": "Cambria",
                    "2": "Times",
                    "3": "Constantia",
                    "4": "Georgia",
                    "5": "SegoeUI",
                    "6": "Candara",
                    "7": "TrebuchetMS",
                    "8": "Verdana",
                    "9": "Consolas",
                    "10": "LucidaConsole",
                    "11": "DejaVuSansMono",
                    "12": "CourierNew",
                    "13": "Courier"
                }
            }

            data = {'p':p}

            response = self.session.post(url,data=data)

            return True

        except Exception, e:
            e.message += ('function : endclothing ---> verify')
            raise 
