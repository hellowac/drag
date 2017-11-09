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
            area = pqhtml('.product-details')
            Jtxt = pqhtml('script').text()
            pdata = self.get_pdata(Jtxt)

            #下架
            if not pdata['ChoiceGroups'] :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            if len(pdata['ChoiceGroups']) > 1 :
                raise ValueError('ChoiceGroups length great than one')

            detail = dict()

            #名称
            detail['name'] = pdata['Title']

            #品牌
            detail['brand'] = pdata['Brand']['Name']

            #颜色
            color,colorId = self.get_color(pdata)
            detail['color'] = color
            detail['colorId'] = colorId

            #钥匙
            detail['keys'] = color.keys()

            #图片集
            imgs = self.get_imgs(pdata)
            detail['img'] = imgs[0] if isinstance(imgs,list) else dict([ (cid,Arr[0]) for cid,Arr in imgs.items() ])
            detail['imgs'] = imgs

            #货币
            currency = pdata['CurrencyCode']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #产品ID
            productId = pdata['Id']
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(pdata,color)

            #描述
            detail['descr'] = pdata['Description']

            # print json.dumps(pdata)

            #价格
            detail['price'] = pdata['LowPrice']
            # detail['listPrice'] = pdata['HighPrice']
            detail['listPrice'] = pdata['ChoiceGroups'][0]['Price']['OriginalPrice'][1:]

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


    def get_sizes(self,pdata,color):
            
        skus = pdata['Skus']
        cid_dic = dict([(v,k) for k,v in color.items()])
        manyGroup = len(pdata['ChoiceGroups'])>1

        sizes = {}
        if skus :
            for sku in skus :
                cid = cid_dic[sku['Color']]
                size = sku['Size']
                width = sku.get('Width','')
                filte = sku.get('Filter','')

                if width :
                    size = width+' '+size

                if manyGroup and filte :
                    size = filte+' '+size

                obj = {'name':size,'inventory':self.cfg.DEFAULT_STOCK_NUMBER,'sku':sku['Id'],'price':sku['Price'][1:]}

                if cid in sizes :
                    sizes[cid].append(obj)
                else :
                    sizes[cid]=[obj]

        if sizes :
            return sizes

        raise ValueError,'Get sizes Fail'

    def get_imgs(self,pdata):
            
        medials = pdata['StyleMedia']

        imgs = {}
        if medials :
            for medial in medials :
                if medial['MediaType'] == 'Image' :
                    cid = medial['ColorId']
                    url = medial['ImageMediaUri']['Zoom'] if medial['ImageMediaUri']['Zoom'] else medial['ImageMediaUri']['Large']
                    cname = medial['ColorName']

                    if cid in imgs :
                        imgs[cid].append(url)
                    else :
                        imgs[cid] = [url]

        if not imgs :
            medial = pdata['DefaultMedia']
            if medial['MediaType'] == 'Image' :
                url = medial['ImageMediaUri']['Zoom'] if medial['ImageMediaUri']['Zoom'] else medial['ImageMediaUri']['Large']
                imgs = [url]

        if not imgs :
            raise ValueError,'Get Imgs Fail'

        return imgs


    def get_color(self,pdata):
            
        groups = pdata['ChoiceGroups']

        # assert len(groups) == 1

        group = groups[0]

        colors = group['Color']

        color_dic = dict([(color['Id'],color['Value']) for color in colors])
        colorId_dic = dict([(color['Id'],color['Id']) for color in colors])

        if color_dic :
            return color_dic,colorId_dic

        raise ValueError,'Get Colors Fail'


    def get_pdata(self,Jtxt):
            
        ProductPageDesktop = re.search(
            r'React\.render\(React\.createElement\(ProductPageDesktop, ({.*?})\),', Jtxt, re.DOTALL)

        if ProductPageDesktop is None:
            ProductPageDesktop = re.search(
                r'React\.render\(React\.createElement\(product_desktop, ({.*?})\),', Jtxt, re.DOTALL)
        
        if ProductPageDesktop is None:
            ProductPageDesktop = re.search(
                r'React\.render\(React\.createElement\(ProductDesktop, ({.*?})\),', Jtxt, re.DOTALL)

        if ProductPageDesktop :
            StyleModel = json.loads(ProductPageDesktop.groups()[0])['initialData']['Model']['StyleModel']

            return StyleModel

        raise ValueError,'Get styleModel by pageData Fail'

