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
            area = pqhtml('.body-wrap .primary-wrap .product-area')
            domain = tool.get_domain(url)
            siteObj = self.get_siteObj(pqhtml)
            
            print area.outerHtml().encode('utf-8')
            # exit()

            #下架
            if 'InStock' != area('meta[itemprop="availability"]').attr('content') or 'sold out' in area('.availability').text().lower() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #产品ID
            productId = area('input[class="buy"][name="buy"][type="hidden"]').attr('value') or self.get_product_id(siteObj)
            detail['productId'] = productId

            #品牌
            brand = self.get_brand(siteObj)
            detail['brand'] = brand

            #名称
            detail['name'] = area('.product-title').text()

            #货币
            currency = pqhtml('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色,图片,尺码信息
            if area('.variation-dropdowns') :
                img,imgs,color,sizes = self.get_color_img_size(area,productId)
                detail['keys'] = color.keys()
            else :
                img = area('.main-product-image a').attr('href')
                imgs = [ li_a.attr('href').strip().replace('/300/300/','/600/600/') for li_a in area('ul.product-thumbnails li a').items()]
                color = self.cfg.DEFAULT_ONE_COLOR
                sizes = [dict(name=self.cfg.DEFAULT_ONE_SIZE,id=productId,sku=productId,inventory=self.cfg.DEFAULT_STOCK_NUMBER)]

            #颜色
            # color = self.get_color(area)
            detail['color'] = color
            detail['colorId'] = {cid:cid for cid in color.keys()} if isinstance(color,dict) else productId

            #图片集
            detail['img'] = img
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = sizes

            #描述
            detail['descr'] = area('div[itemprop="description"]').text() + area('div.product-more-details').text()

            #详细
            detail['detail'] = area('div.product-more-details').text()

            #退换货
            detail['returns'] = area('.product-delivery-returns').text()

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

    def get_siteObj(self,pqhtml):
        for ele in pqhtml('script').items():
            if 'var siteObj' in ele.text() :
                data = ele.text();
                break;
        else :
            raise ValueError('get data Fail')

        return data

    def get_brand(self,siteObj):
        
        brand = re.search(r'productBrand: "(.*)",',siteObj).groups()[0] 

        if not brand :
            raise ValueError('get brand fail')

        return brand

    def get_product_id(self,siteObj):
        productid = re.search(r'productID: "(.*)",',siteObj).groups()[0]

        if not productid :
            raise ValueError('get productid fail!')

        return productid

    def get_all_price(self,area):
        price = area('meta[itemprop="price"]').attr('content')
        listPrice = price

        if 'Save' in area('.saving-amount').text() :
            savePrice = re.search(r'(\d[\d.]*)',area('.saving-amount').text(),re.DOTALL).groups()[0]
            listPrice = str(float(listPrice) + float(savePrice))

        return price,listPrice

    def get_color_img_size(self,area,pid):
        post_url = 'http://www.mybag.com/variations.json?productId={0}'.format(pid) #11243624

        data = dict(
            selected=1,         #1,选择尺码,2,选择颜色.
            variation1=1,       #1,尺码
            option1=5716,       #尺码ID
            # variation2=2,   #2,颜色
            # option2=141,    #颜色ID
        )

        #尺码节点
        size_eles = area('select#opts-1 option[value!=""]').items()

        colors = dict()
        sizes = dict()
        imgs = dict()
        pimg = dict()
        for ele in size_eles:
            size_id = ele.attr('value')
            size_name = ele.attr('rel')

            data.update(selected=1)
            data.update(variation1=1)
            data.update(option1=size_id)

            resp = self.session.post(post_url,data=data)

            # print resp.text
            respj = resp.json()

            #价格
            price = re.search(r';(\d[\d\.]*)',respj['price']).groups()[0] if ';' in respj['price'] else float(respj['price'])
            listPrice = respj['rrp']

            color_size,color_name = self.handle_variants(respj['variations'],price,listPrice)

            #获取图片
            tmp_imgs = []
            tmp_pimg = ''
            for img in respj['images'] :
                if img['index'] == 0 and img['type'] == 'zoom':
                    tmp_pimg = 'http://s4.thcdn.com/'+img['name']
                    tmp_imgs.append('http://s4.thcdn.com/'+img['name'])
                elif img['type'] == 'zoom' :
                    tmp_imgs.append('http://s4.thcdn.com/'+img['name'])

            #填充size
            for color_id,csizes in color_size.items() :
                if color_id not in sizes :
                    sizes[color_id] = csizes        #sizes[color_id] list类型
                else :
                    sizes[color_id].extend(csizes)

            #填充color
            for color_id,cname in color_name.items():
                if color_id not in colors :
                    colors[color_id] = cname        #sizes[color_id] string类型

                if color_id not in imgs :
                    imgs[color_id] = tmp_imgs

                if color_id not in pimg :
                    pimg[color_id] = tmp_pimg

        return pimg,imgs,colors,sizes

    def handle_variants(self,variants,price,listPrice):
        colors = []
        sizes = []

        for variant in variants :
            if variant['variation'] == 'Colour' :
                colors = [ dict(cname=opt['name'],cid=opt['id']) for opt in variant['options']]

            elif variant['variation'] == 'Size' :
                sizes = [ dict(sname=opt['name'],sid=opt['id']) for opt in variant['options']]

        if not colors or not sizes :
            raise ValueError('get color or size fail, variants:{0}'.format(variants))

        color_size = dict()        
        color_name = dict()

        for c in colors :
            color_id = str(c['cid'])
            color_size[color_id] = list()
            color_name[color_id] = c['cname']

            for s in sizes :
                color_size[color_id].append(dict(name=s['sname'],sku=s['sid'],id=s['sid'],price=price,listPrice=listPrice,inventory=self.cfg.DEFAULT_STOCK_NUMBER))

        return color_size,color_name



        












