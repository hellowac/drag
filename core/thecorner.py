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
import re
import json
import time

#该渠道已关闭.20160-12-16

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

            if pqhtml('#info404').text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            if status_code != 200 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            area = pqhtml('article#itemCentral')

            # print area.outerHtml()
            # exit()

            #固定价格符号
            if 'www.thecorner.com.cn/cn/' not in url :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('DOMAINERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            #判断下架
            color_params = area('div.colors div.selectColorAlert').attr('data-ytos-opt')
            not_avali = len('#itemData div.notAvailMessage')

            if not color_params and not_avali > 0 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            #获取pdata
            domain = tool.get_domain(url)
            link = domain + '/yTos/api/Plugins/ItemPluginApi/GetCombinations'
            pdata = self.get_pdata(color_params,link)


            detail = dict()

            #品牌
            brand = area('h2.brandNameTitle').text()
            detail['brand'] = brand

            #名称
            detail['name'] = brand+' '+area('div.productInfo span.microCategory').text()

            #货币单位,该网站就是com.cn
            currency = 'CNY'
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            detail['price'] = area('div.productInfo span.price:last span.value').attr('data-ytos-price')
            detail['listPrice'] = area('div.productInfo span.price:first span.value').attr('data-ytos-price')

            #描述
            detail['descr'] = area('#itemData ul.tabs li').text()

            #图片
            imgsTmp = self.get_imgs(area)
            detail['img'] = imgsTmp[0]
            detail['imgs'] = imgsTmp

            #季节系列
            detail['seasonPremise'] = area('div.seasonLabel').text()

            #构造
            detail['fabric'] = area('li[data-ytos-tab="Details"] div.compositionInfo').text()

            #细节
            detail['detail'] = area('li[data-ytos-tab="Details"] div.itemdescription').text()

            #退换货
            detail['returns'] = area('li[data-ytos-tab="ShippingReturns"]').text()

            #产品ID
            detail['productId'] = area('div.priceUpdater').attr('data-ytos-scope')

            #规格
            keys,colorId,colorName,sizes = self.get_sizes(pdata)
            detail['keys'] = keys
            detail['sizes'] = sizes
            detail['color'] = colorName
            detail['colorId'] = colorId

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

    def get_sizes(self,pdata):
        colorName = dict([(color['ColorId'],color['Description']) for color in pdata['Colors']])

        colorId = dict([(color['ColorId'],color['ColorId']) for color in pdata['Colors']])

        keys = colorId.keys()

        sizes = dict()

        for cs in pdata['ModelColorSizes'] :
            key = cs['Color']['ColorId']
            obj = dict(name=cs['Size']['Description'],inventory=cs['Quantity'],sku=cs['Size']['Size'])

            if key in sizes : 
                sizes[key].append(obj)
            else :
                sizes[key] = [obj]

        return keys,colorId,colorName,sizes


    def get_pdata(self,color_params,link):
        params = dict()
        params.update(json.loads(color_params)['options'])

        resp = self.session.get(link,params=params, verify=False)

        return json.loads(resp.text)


    def get_imgs(self,area):
        eles = area('#itemImages ul.alternativeImages li img')
        return [img.attr('src').replace('_8_','_14_') for img in eles.items()] 



