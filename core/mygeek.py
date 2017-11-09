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
        # area = pqhtml('.product-detail-information')
        self.domain = tool.get_domain(url)
        # pdata = self.get_pdata(area)
        
        # print pqhtml.outerHtml().encode('utf-8')
        # exit()

        #下架
        # if True :

            # log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            # self.logger.info(log_info)
            # data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
            
            # return tool.return_data(successful=False, data=data)

        detail = dict()

        #品牌
        brand = self.getBrandByHtml(pqhtml).strip()
        detail['brand'] = brand or 'MYGEEK'

        #名称
        detail['name'] = pqhtml('span.title strong').text().strip()

        #货币
        currency = 'CNY'
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        #价格
        price,listPrice = self.getPriceByHtml(pqhtml)
        detail['price'] = price
        detail['listPrice'] = listPrice

        #颜色
        color = self.get_color(pqhtml)
        detail['color'] = color
        detail['colorId'] = { k:k for k in color.keys() } if isinstance(color,dict) else self.cfg.DEFAULT_COLOR_SKU

        #skus:
        if isinstance(color,dict):
            detail['keys'] = color.keys()

        #图片集
        imgs = self.getImgsByHtml(pqhtml)
        detail['img'] = imgs[0]
        detail['imgs'] = imgs

        #产品ID
        productId = re.search(r'id=(\d*)',pqhtml('div.pid5 form:first').attr('action')).groups()[0]
        detail['productId'] = productId

        #规格
        detail['sizes'] = self.getSizesByHtml(pqhtml)

        #描述
        detail['descr'] = pqhtml('#pid1_2').remove('.title').remove('script').text() + pqhtml('.pid2').remove('.title').remove('script').text()

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

    def get_color(self,pqhtml):
        pid1_2 = pqhtml('#pid1_2')

        eles = pqhtml('form[name="formx"] div[class^="sdiv1"]')

        if len(eles) and u'颜色' in pid1_2.text() :
            color = {ele('span').text():ele('span').text() for ele in eles.items() if ele('span').text() } or self.cfg.DEFAULT_ONE_COLOR
        else :
            color = self.cfg.DEFAULT_ONE_COLOR

        return color



    def getSizesByHtml(self,pqhtml):
        inv = self.cfg.DEFAULT_STOCK_NUMBER if pqhtml('#pid1_2 form') else 0

        elements = pqhtml('#pid1_2 span')
        for ele in elements.items() :
            if u'尺寸' in unicode(ele.text()) :
                sizes = ele.next()('div[class!=""]')
                sizes = [e.text() for e in sizes.items() if e.text() ]
                sizes = map(lambda x : dict(name=x,inventory=inv,sku=x,id=x),sizes)
                break
        else :
            sizes = [dict(name=self.cfg.DEFAULT_ONE_SIZE,sku=self.cfg.DEFAULT_SIZE_SKU,id=self.cfg.DEFAULT_SIZE_SKU,inventory=inv)]
            
        return sizes



    def getImgsByHtml(self,pqhtml):
        imgs = [e.attr('src') for e in pqhtml('#pid1_1_s img').items()] + [ e.attr('src') for e in pqhtml('.pid2 img').items() if e.attr('src') ] 

        def f(x):
            if x and x[0] == '/' :
                return self.domain+x

            elif x and x[0] == 'h' :
                return x

            raise ValueError,'Error Img Src %s' %x

        imgs = map(f,imgs)

        return imgs


    def getPriceByHtml(self,pqhtml):
        elements = pqhtml('#pid1_2 span')
        for ele in elements.items() :
            if u'麦极价：' in unicode(ele.text()) :
                price=ele('strong').text()[1:]
                break
        else :
            price = 0

        return price,price
        

    def getBrandByHtml(self,pqhtml):
        elements = pqhtml('#pid1_2 span')
        for ele in elements.items() :
            if u'品牌：' in unicode(ele.text()) :
                brand = unicode(ele.text()).split(u'：')[1]
                break
        else :
            brand = 'MYGEEK'

        return brand


