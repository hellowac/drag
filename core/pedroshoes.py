#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/07"

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
            area = pqhtml('.product-essential')

            #下架
            if 'notify me when back in stock' in area('.alert-stock').text().lower() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)
        
            pdata = self.get_pdata(area)

            # print json.dumps(pdata)
            # exit()

            detail = dict()

            #品牌
            brand = 'PEDRO'
            detail['brand'] = brand

            #名称
            detail['name'] = area('.product-name').text()



            #货币
            currency = self.get_currency(pdata)
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(pdata)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            color = self.get_color(pdata)
            detail['color'] = color
            detail['colorId'] = dict([ (key,key) for key in color.keys() ])

            #图片集
            imgs = self.get_imgs(color,area)
            detail['img'] = imgs[0] if isinstance(imgs,list) else dict([ (cid,Arr[0]) for cid,Arr in imgs.items() ])
            detail['imgs'] = imgs

            #钥匙
            detail['keys'] = color.keys()

            #产品ID
            productId = pdata['productId']
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(pdata,area)

            #描述
            detail['descr'] = area('.short-description').remove('script').text()

            #退换货
            detail['returns'] = ''


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


    def get_sizes(self,pdata,area):
        colorContact = None
        sizeContact = None
        for k,v in pdata['attributes'].items() :
            if v['code'] == 'size' :
                sizeContact = v['options']
            elif v['code'] == 'color' :
                colorContact = self.get_colorContact(v['options'])

        availabilityOnly = area('p.availability-only')

        sizes = {}
        for cid,item in colorContact.items() :
            #该颜色无库存.
            if not item['in'] and not item['out']:
                sizes[cid] = [{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':0,'sku':self.cfg.DEFAULT_SIZE_SKU}]

            elif item['in'] or item['out']:
                #---有库存的.
                for pid in item['in'] :
                    sizeName = self.get_sizeName_by_json(sizeContact,pid)
                    inventory = self.get_inv_by_html(availabilityOnly,pid)

                    obj = {'name':sizeName,'inventory':inventory,'sku':pid,'id':pid}
                    if cid in sizes :
                        sizes[cid].append(obj)
                    else :
                        sizes[cid] = [obj]

                #---没库存的.
                for pid in item['out'] :
                    sizeName = self.get_sizeName_by_json(sizeContact,pid)

                    pid = pid.replace('-','')           #前面带-号表示无库存

                    obj = {'name':sizeName,'inventory':0,'sku':pid,'id':pid}
                    if cid in sizes :
                        sizes[cid].append(obj)
                    else :
                        sizes[cid] = [obj]

        return sizes


    def get_inv_by_html(self,pyhtml,Pid):
            
        defualtInv = pyhtml.prev()('select#qty option:last').attr('value')

        inv = pyhtml('span#stock_qty_{pid}>strong'.format(pid=Pid)).text()

        if inv :
            inv = int(inv)
            return inv

        return defualtInv


    def get_sizeName_by_json(self,Arr,Pid):
        sizeName = None
        for size in Arr :
            if Pid in size['products'] :
                sizeName = size['label']
                break
        else :
            raise ValueError,'Get sizeName Fail,Pid is {pid}'.format(pid=Pid)
        
        return sizeName


    def get_imgs(self,color,area):
            
        imgs = {}
        for k in color :
            imgAs = area('.more-views ul.attribute_{key}>li>a'.format(key=k))
            imgArr = [a.attr('href') for a in imgAs.items()]
            imgs[k] = imgArr

        if imgs :
            return imgs

        raise ValueError,'Get Imgs Fail'



    def get_color(self,pdata):
            
        color = None
        for k,v in pdata['attributes'].items() :
            if v['code'] == 'color' :
                color = dict([(opt['id'],opt['label']) for opt in v['options']])
                break
        else :
            raise ValueError,'Get Colors Fail'

        return color


    def get_colorContact(self,Arr):
        colorContact = {}
        for color in Arr :
            cid = color['id']
            InStock = filter(lambda x : x[0] != '-',color['products'])
            OutStock = filter(lambda x : x[1:] not in InStock,filter(lambda x : x[0] == '-',color['products']))

            colorContact[cid]={'in':InStock,'out':OutStock}
        return colorContact


    def get_all_price(self,pdata):
        price = pdata['basePrice'].replace(',','').strip()
        listPrice = pdata['oldPrice'].replace(',','').strip()

        if price and listPrice :
            return price,listPrice

        raise ValueError,'Get Price Fail'


    def get_currency(self,pdata):
        template = pdata['template']

        currency = None

        if template[:3] == 'HK$' :

            currency = 'HKD'

        elif template :
            unit = template.split('#')[0]
            currency = {u'£':'GBP',u'€':'EUR'}[unit]

        if not currency:
            raise ValueError,'Get Unit Fail'

        return currency


    def get_pdata(self,area):
            
            Jtxt = area('.product-options script').text()

            config = re.search(r'spConfig = new Product.Config\((.*?)\);',Jtxt,re.DOTALL)

            if config :
                config = json.loads(config.groups()[0])

                return config

            raise ValueError,'Get Product Config Fail'



