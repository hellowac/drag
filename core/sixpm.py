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
            area = pqhtml('#theater')
            domain = tool.get_domain(url)
            pdata = self.get_pdata(pqhtml('script:gt(20)'))
            
            # exit()

            #下架
            # if True :

                # log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                # self.logger.info(log_info)
                # data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                # return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = area('.brand').text()
            detail['brand'] = brand

            #名称
            detail['name'] = area('h1:first').text()


            currencySymbol,price,listPrice = self.get_price_info(pdata)

            if currencySymbol != '$' :
                raise ValueError('currencySymbol is not USD')

            #货币
            currency = 'USD'
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            color = self.get_color(pdata)
            detail['color'] = color
            detail['colorId'] = {cid:cid for cid in color.keys() }

            #图片集
            img,imgs = self.get_imgs(pdata)
            detail['img'] = img
            detail['imgs'] = imgs

            #产品ID
            productId = pqhtml('input[name="productId"]').attr('value')
            detail['productId'] = productId

            #规格
            sizes = self.get_sizes(pdata)
            detail['sizes'] = sizes

            #描述
            detail['descr'] = area('.description').text()

            detail['keys'] = set(img.keys())&set(sizes.keys())

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

    def get_pdata(self,elements):
        
        for ele in elements.items() :
            if ele.text()[16:33] == 'private namespace' :
                return ele.text()

        raise ValueError,'Get pdata Fail'


    def get_price_info(self,pdata):
        r = re.search(r'var\s*(colorPrices =\s*\{.*?\})\s*;',pdata,re.DOTALL)

        if r :
            exec r.groups()[0]
            unit = colorPrices.values()[0]['now'][0]
            price = dict([(cid,item['nowInt']) for cid,item in colorPrices.items()])
            oldPrice = dict([(cid,item['wasInt']) for cid,item in colorPrices.items()])
            return unit,price,oldPrice

        raise ValueError,'Get PriceFail'

    def get_imgs(self,pdata):
        
        r = re.search(r'(colorIds =.*?})\s*;',pdata,re.DOTALL)
        if r :
            exec r.groups()[0]
        else :
            raise ValueError,'Get colorIds Fail'

        r = re.search(r'(pImgs =.*?)\s*z.facelift',pdata,re.DOTALL)
        if r :
            width='width'
            height='height'
            filename='filename'
            exec r.groups()[0]

            imgs = dict([(str(colorIds[str(cid)]),[v['filename'] for k,v in item['4x'].items()] if item['4x'] else [x.values() for x in item['2x']]) for cid,item in pImgs.items()])
            
            #exec 还不能和字典推导在一个函数中...
            img = dict([(str(colorIds[str(cid)]),item['4x']['p']['filename']) if '4x' in item else item['2x']['p'] for cid,item in pImgs.items() ])

            for cid,arr in imgs.items():
                arr.sort()
                arr.insert(0,arr.pop())

            return img,imgs

        raise ValueError,'Get Imgs Fail'


    def get_color(self,pdata):
        
        r = re.search(r'(colorNames\s*=\s*\{.*?\})\s*;',pdata,re.DOTALL)
        if r :
            exec r.groups()[0]
            return colorNames

        raise ValueError,'Get colors Fail'

    def get_sizes(self,pdata):
        
        #库存sku信息
        r = re.search(r'(stockJSON\s*=.*?);\s*var',pdata,re.DOTALL)
        if r :
            exec r.groups()[0]
            stockJSON = json.dumps(stockJSON)
        else :
            raise ValueError,'Get stockJSON Fail'

        #尺寸ID对应的值
        r = re.search(r'(valueIdToNameJSON\s*=.*?);\s*var',pdata,re.DOTALL)
        if r :
            exec r.groups()[0]
        else :
            raise ValueError,'Get valueIdToNameJSON Fail'

        #尺寸ID转换
        r = re.search(r'(dimensionIdToNameJson\s*=.*?);\s*var',pdata,re.DOTALL)
        if r :
            exec r.groups()[0]

            for k,v in dimensionIdToNameJson.items():
                stockJSON = stockJSON.replace('"{k}"'.format(k=k),'"{v}"'.format(v=v))
            stockJSON = json.loads(stockJSON)
        else :
            raise ValueError,'Get dimensionIdToNameJson Fail'

        #one size 只有颜色
        if not dimensionIdToNameJson and not valueIdToNameJSON and stockJSON :
            return dict([(item['color'],[{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':item['onHand'],'sku':item['id'],'id':item['id']}]) for item in stockJSON])

        sizes = {}
        widths = len(set([ item.get('width','') for item in stockJSON])) > 1        #width种类大于1 才累加到size后面.

        for item in stockJSON :
            inv = item['onHand']
            cid = item['color']
            sku=sid=item['size']
            width = item.get('width','')

            try:
                size = valueIdToNameJSON[sid]['value']
                if width and widths : 
                    size = size+' '+valueIdToNameJSON[width]['value']
            except KeyError, e:
                continue
                # raise

            obj = dict(name=size,sku=sku,id=sid,inventory=inv)

            if cid in sizes :
                sizes[cid].append(obj)
            else :
                sizes[cid]=[obj]

        return sizes
