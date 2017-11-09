#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/29"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
import re
import json
import time
try:
    # Python 2.6-2.7 
    from HTMLParser import HTMLParser
except ImportError:
    # Python 3
    from html.parser import HTMLParser


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

            #下架:
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
            Jtxt = pqhtml('script').text()
            area = pqhtml('#itemContent')

            # print area.outerHtml().encode('utf-8')

            #下架
            if not area :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)


            pdata = json.loads(re.search(r'jsInit.item.colorSizeJson =\s*(.*?\}\});\s*',Jtxt,re.DOTALL).groups()[0])
            
            detail = dict()

            #名称:
            name = re.search(r'tc_vars\["product_title"\] =\s*"(.*?)";',Jtxt,re.DOTALL).groups()[0]
            # name = json.loads(u'[{0}]'.format(HTMLParser().unescape(name)))[0]
            detail['name'] = area('#itemTitle').text()

            #品牌
            brand = re.search(r'tc_vars\["product_brand"\] =\s*"(.*?)";',Jtxt,re.DOTALL).groups()[0]
            detail['brand'] = area('#itemTitle span[itemprop="brand"]').text() or brand

            #货币符号
            currency = re.search(r'tc_vars\["nav_currency"\] =\s*"(.*?)";',Jtxt,re.DOTALL).groups()[0]
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            detail['price'] = re.search(r'tc_vars\["product_discountprice"\] =\s*"(.*?)";',Jtxt,re.DOTALL).groups()[0]
            detail['listPrice'] = re.search(r'tc_vars\["product_price"\] =\s*"(.*?)";',Jtxt,re.DOTALL).groups()[0]

            #图片集
            imgsTmp = self.get_imgs(Jtxt,area,pdata)
            detail['img'] = dict([ (cid,imgs[0]) for cid,imgs in imgsTmp.items() ]) if isinstance(imgsTmp,dict) else imgsTmp[0]
            detail['imgs'] = imgsTmp

            #规格
            detail['sizes'] = self.get_sizes(pdata)

            #产品ID
            detail['productId'] = dict([ (color['Cod10'],color['Cod10']) for color in pdata['Colors']])

            #颜色
            detail['color'] = dict([(color['Cod10'],color['Name']) for color in pdata['Colors']])
            detail['colorId'] = dict([ (color['Cod10'],color['Cod10']) for color in pdata['Colors']])

            #描述,2016-09-25 12:31:54 修改
            detail['descr'] = area('#item-infos li:first').remove('script').text()
            # detail['descr'] = area('#itemInfoTab #tabs-1').remove('script').text()

            #构造物,2016-09-25 12:31:54 修改
            detail['fabric'] = area('#item-infos li:first').remove('script').text()
            # detail['fabric'] = area('#item-infos #tabs-1').remove('script').text()

            #退换货,2016-09-25 12:31:54 修改
            detail['returns'] = area('#item-infos li:last').remove('script').text()
            # detail['returns'] = area('#item-infos #tabs-3').remove('script').text()

            #设计者
            detail['designer'] = re.search(r'tc_vars\["product_author"\] =\s*"(.*?)";',Jtxt,re.DOTALL).groups()[0]

            #钥匙
            detail['keys'] = [ color['Cod10'] for color in pdata['Colors']]

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



    def get_sizes(self,pdata):
        
        try:
            color_sizeArr = dict([(color['Cod10'],color['Sizes']) for color in pdata['Colors']])

            sizeId2Name = dict([(size['Id'],size['Name']) for size in pdata['Sizes']])

            Qty = pdata['Qty']

            sizes = {}
            for cod10,sizeArr in color_sizeArr.items() :
                Arr = []
                for sid in sizeArr :
                    try:
                        key = '{cod10}_{sid}'.format(cod10=cod10,sid=sid)
                        inv = Qty[key]
                        Arr.append(dict(name=sizeId2Name[sid],inventory=inv,id=cod10,sku=sid))
                    except Exception, e:
                        raise ValueError,'getSizesByColorSizeJson key {key} not found!'.format(key=key)
                    
                sizes[cod10]=Arr
                
            return sizes

        except Exception, e:
            raise


    def get_imgs(self,Jtxt,area,pdata):
        # imgpath = re.search(r'IMG_PRODUCT_PATH:\s*\'(.*?)\',',Jtxt,re.DOTALL).groups()[0]

        # print area.outerHtml().encode('utf-8')
        # print json.dumps(pdata)

        imgpath = re.search(r'IMG_PRODUCT_PATH:\s*"(.*?)",',Jtxt,re.DOTALL).groups()[0]

        imgElements = area('ul#itemThumbs>li>img')

        if len(imgElements) > 0 :
            imgs = map(lambda x : x.split('//')[1] , [img.attr('src') for img in imgElements.items()])

            imgs = map(lambda x : x[x.find('/')+1:].replace('_9_','_14_'),imgs)

            imgs = map(lambda x : imgpath+x,imgs)

            cod10 = re.search(r'/([\d\w]*)_14_\w',imgs[0],re.DOTALL).groups()[0]

            imgArr = dict()

            for color in pdata['Colors'] :
                colorCod10 = color['Cod10']
                imgArr[colorCod10] = map(lambda x: x.replace(cod10,colorCod10.lower()),imgs)

        else :

            #获取多颜色,但只有一张图片的商品 #http://www.yoox.cn/cn/46469632VA/item
            #http://www.yoox.cn/cn/46460729TF/item
            imgArr = dict()

            for ele in area('div#itemColors ul>li').items() :
                colorCod10 =ele.attr('id').replace('color','')

                src = ele('img').attr('src')
                colonIndex = src.find(':')

                sindex = src.find('/',colonIndex+3,)

                subSrc = src[sindex+1:]

                subSrc = subSrc.replace('_18_','_14_')

                imgArr[colorCod10] = [imgpath+subSrc]

            # imgArr = [area('#itemImage #openZoom img:first').attr('src')]

        if not imgArr :
            raise ValueError,'get ImgArr Fail'

        return imgArr

    

