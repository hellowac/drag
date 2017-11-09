#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/28"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
import re
import json
import time
import demjson as djson

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

            if len(pqhtml('#search_string_not_found')) > 0 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            if status_code != 200 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            Jtxt = pqhtml('script').text()

            #获取pdata
            pdata = self.get_pdata(Jtxt)
            outStock = pqhtml('#item_out_of_stock')
            variables = self.get_variables(Jtxt)

            #下架
            if pdata is None and len(outStock) > 0 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #名称
            detail['name'] = variables['product']['name']

            #货币符号
            currency = variables['product']['currency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price = variables['product']['unit_sale_price']
            listPrice = variables['product']['unit_price'] or variables['product']['unit_sale_price']
            detail['price'] = price
            detail['listPrice'] = listPrice if listPrice >= price else price

            #品牌
            detail['brand'] = 'TOPMAN'

            #描述
            detail['descr'] = self.get_descr(pdata)

            #图片
            imgsTmp = self.get_imgs(pdata)
            detail['img'] = imgsTmp[0]
            detail['imgs'] = imgsTmp

            #产品ID
            detail['productId'] = pdata['id']                                  #re.search(r'id:\s*"(\d*)",',pdata,re.DOTALL).groups()[0]
            detail['productCode'] = pdata['code']
            detail['productSku'] = variables['product']['sku_code']

            #规格
            detail['sizes'] = self.get_sizes(pdata)

            #颜色
            detail['color'] = variables['product']['color']
            detail['colorId'] = pdata['productAttributes']['COLOUR_CODE'] or variables['product']['id'] or variables['product']['sku_code']

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url
            
            #返回的IP和端口
            if resp.raw._original_response.peer :
                detail['ip_port']=':'.join(map( lambda x:str(x),resp.raw._original_response.peer))

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)

            return tool.return_data(successful=True, data=detail)

        except Exception:
            raise


    def get_sizes(self,pdata):
        Skus = pdata['SKUs']

        if not Skus :
            raise ValueError,'Skus is None'

        # sizes = re.findall(r'\{value:\s*"(.*?)",\s*partnumber:\s*"(.*?)",\s*availableinventory:\s*"(.*?)",\s*skuid:\s*"(.*?)",\s*defining:\s*"Size"\}',Skus,re.DOTALL)  #找出所有的size

        sizes = [dict(
                    name=SKU['value'] if SKU['value'] != '000' else self.cfg.DEFAULT_ONE_SIZE ,
                    inventory=SKU['availableinventory'],
                    sku=SKU['skuid'],
                    value=SKU['value'],
                    id=SKU['skuid'],
                    ) 
                for SKU in Skus ]

        # return [ {'name':size[0] if size[0] != '000' else self.cfg.DEFAULT_ONE_SIZE,'inventory':int(size[2]),'sku':size[3],'id':size[3]} for size in sizes ]
        
        if not sizes :
            raise ValueError('get sizes fail')

        return sizes


    def get_imgs(self,pdata):
        imageUrls = pdata['imageUrls']

        if not imageUrls :
            raise ValueError,'imageUrls is None'

        return [img['large'] for img in imageUrls['Thumbnailimageurls']]


    def get_descr(self,pdata):

        description = pdata['description']

        if not description:
            raise ValueError,'description is None'

        return PyQuery(PyQuery(description).text()).text()


    def get_variables(self,Jtxt):
        r = re.search(r'window.universal_variable =\s*(\{.*?\}\s*\})\s*',Jtxt,re.DOTALL)

        if r is not None :
            try:
                exec 'data='+r.groups()[0]
                return data
            except SyntaxError, e:
                exec 'data='+r.groups()[0].replace('"/>','')
                return data
        else:
            raise ValueError,'UniversalVariable is None'


    def get_pdata(self,Jtxt):
        g = re.search(r'var productData =\s*(\{.*?\})\s*Arcadia.Page.baseUrl',Jtxt,re.DOTALL)

        if g :
            return djson.decode(g.groups()[0])
        else:
            return None
