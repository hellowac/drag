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

            if status_code != 200 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            instock = len(pqhtml('input#buyButton'))

            #下架:
            if not instock :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

            Jtxt = pqhtml('script').text()
            area = pqhtml('div#pageContent')

            digitalData = self.get_DigitalData(Jtxt)
            pDetail = self.get_pDetail(Jtxt)

            detail = dict()

            #产品ID
            detail['productId'] = area('div#productId').text()

            #品牌
            detail['brand'] = area('h1 a[itemprop="brand"]').text()

            #名称
            detail['name'] = area('#product-information h1').text()

            #描述
            detail['descr'] = area('#detailsAccordion div[itemprop="description"]').text()

            #尺码描述
            detail['sizeFit'] = self.get_sizing(area) #pyhtml('#detailsAccordion div#modelSizeFitDescription').text()

            #产品设计
            detail['designer'] = area('#detailsAccordion div#designerContainer').text()

            #退换货
            detail['returns'] = area('#detailsAccordion div#designerContainer').nextAll('div').text()

            #价格符号
            currency = digitalData['page']['attributes']['currency']
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #图片,size和color映射
            cid_models, cid_names, cid_imgs, csMap = self.get_ISArr(pDetail['colors'], digitalData)

            #产品价格
            price,listPrice = self.get_all_price(area,cid_names)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #模特信息
            detail['model'] = cid_models

            #产品尺码:
            detail['sizes'] = self.get_sizes(pDetail['sizes'],csMap)

            #产品图片
            detail['imgs'] = cid_imgs
            
            #产品分解Keys,多颜色
            if cid_imgs :
                detail['keys'] = cid_imgs.keys()
                detail['img'] = dict([(key,ls[0]) for key,ls in cid_imgs.items() ])
                detail['color'] = cid_names   #多颜色
                detail['colorId'] = dict([ (cid,cid) for cid in cid_imgs.keys() ])
            else :
                #没有获取到KEY.
                raise ValueError,'get cid_imgs Fail'


            #其他判断
            if not csMap and cid_imgs :             #out of stock
                keys = cid_imgs.keys()
                for color in keys:
                    detail['sizes'][color] = None

            #下架
            if not csMap and not cid_imgs :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)

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
            

    #获取图片，color和size映射
    def get_ISArr(self,pro_colors,digitalData):
        invURL = 'https://www.eastdane.com/actions/availabilityCheck.action'

        product = digitalData['page']['category']['primaryCategory']

        # print json.dumps(digitalData)

        if product and ':' in product :
            product = product.split(':')[1]
        else :
            raise ValueError,'Get product params Fail'

        params = dict(product=product)

        csMap = dict()

        for cid,cValue in pro_colors.items() :

            params.update(color=cid)

            sizeArr = []
            for size in cValue['sizes'] :
                # print size
                params.update(size=size,_=str(int(time.time())*1000))
                response = self.session.get(invURL, params=params, verify=False)
                # print response.text
                inv = json.loads(response.text)['responseData']['available'] or self.cfg.DEFAULT_STOCK_NUMBER

                sizeArr.append({'id':size,'inv':inv})

            cName = cValue['colorName']

            csMap[cid] = sizeArr

        # print csMap

        cid_imgs = dict([(cid,[ img[1]['zoom'] for img in sorted(color['images'].items())]) for cid,color in pro_colors.items() if color['images'] != [] and color['sizes'] != [] ])                 #按官网排序. 
        
        cid_names = dict([(cid,color['colorName']) for cid,color in pro_colors.items() if color['images']]) 

        cid_models = dict([(cid,' '.join(color['model'].values())) for cid,color in pro_colors.items() if isinstance(color['model'],dict) ]) 

        return cid_models,cid_names,cid_imgs,csMap


    # 获取size
    def get_sizes(self, pro_sizes, csMap):
        try:
            # size码名称映射
            sMap = dict([(item['sizeCode'], size)
                         for size, item in pro_sizes.items()])

            # print 'sMap',sMap
            # 颜色sizeArr映射
            size = dict([(cid, [dict(name=sMap[size['id']], inventory=size['inv'], sku=size['id'],id=size['id']) for size in sizeArr ]) for cid, sizeArr in csMap.items()])

            # print 'size',size
            return size

        except Exception, e:
            e.message += ('function : get_sizes')
            raise


    #获取所有价格
    def get_all_price(self,pqhtml,cid_names):
        try:
            pInfor = pqhtml('#product-information')

            listPrice = pInfor('div[itemprop="offers"] meta[itemprop="price"]').attr('content')

            price = dict()

            for block in pInfor('div.priceBlock').items() :
                if len(block('span')) > 0 :
                    color = block('span.priceColors').text()
                    if not color :
                        color = self.cfg.DEFAULT_ONE_COLOR

                    ptxt = block('span.regularPrice').text()
                    if not ptxt :
                        ptxt = block('span.originalRetailPrice').text()
                    if not ptxt :                                  #有折扣
                        ptxt = block('span.salePrice').text()

                    if not ptxt :
                        break 

                    ptxt = re.search(r'(\d[.\d]*)',ptxt.replace(',',''),re.DOTALL).groups()[0]

                    if ',' in color :                               #多个颜色折扣.
                        colors = color.split(',')
                        for name in colors :
                            price[name.strip()] = ptxt
                    else :
                        price[color] = ptxt

            ptxt = pInfor('div.priceBlock').text()

            #价格预警
            if '|' in ptxt :
                ptxt1 = ptxt.split('|')[0].strip()
                ptxt2 = ptxt.split('|')[1].strip()

                price1 = re.search(r'(\d[.\d]*)',ptxt1.replace(',',''),re.DOTALL).groups()[0]
                price2 = re.search(r'(\d[.\d]*)',ptxt2.replace(',',''),re.DOTALL).groups()[0]

                #检查HK$和$的价格是否一样
                if price1 == price2 and ptxt1 != ptxt2:
                    raise ValueError,'eastdane Two prices is Equal !!! price:%s price2:%s' %(ptxt1,ptxt2)

            if not price :
                if '|' in ptxt :
                    price = re.search(r'(\d[.\d]*)',ptxt1.replace(',',''),re.DOTALL).groups()[0]
                else :
                    price = re.search(r'(\d[.\d]*)',ptxt.replace(',',''),re.DOTALL).groups()[0]

            if isinstance(price,dict) :
                _cid = dict([ (name,cid) for cid,name in cid_names.items() ])
                _price = dict()
                for name,p in price.items() :
                    try:
                        _price[_cid[name]] = p
                    except KeyError, e:
                        if e.message == self.cfg.DEFAULT_ONE_COLOR :
                            continue
                        else :
                            raise
                price = _price

            return price,listPrice

        except Exception, e:
            e.message += ('function : get_all_price')
            raise
        

    #获取尺码规格
    def get_sizing(self,pqhtml):
        try:
            message = pqhtml('#sizeFitContainer p').text()

            sizing = None

            #有sizeing
            # if message :
            #     table = pqhtml('table')
            #     trOne = table('tr:first')
            #     trNextAll = trOne.nextAll('tr')
            #     tArr = [ t.text() for t in trOne('th').items()]
            #     toArr = [ [ t.text() for t in ot('td').items() ] for ot in trNextAll.items()]

            #     a = map(lambda t: dict(zip(t,tArr)),toArr)

            #     sizing = dict(text=message,data=dict(title=tArr,array=toArr),map=a)                

            # return sizing
            return pqhtml('#sizeFitContainer').text()

        except Exception, e:
            e.message += ('function : get_sizing')
            raise


    #获取产品详情数据
    def get_pDetail(self,Jtxt):
        try:
            g = re.search(r'var productDetail=\s*(.*?);\s*var productPage',Jtxt,re.DOTALL)

            if not g :
                raise ValueError,'search productDetail Fail'

            return json.loads(g.groups()[0])

        except Exception, e:
            e.message += ('function : get_pDetail')
            raise


    #获取数字数据
    def get_DigitalData(self,Jtxt):
        try:
            digitalData = re.search(r'var digitalData =\s*(\{.*?\}\})\s*;',Jtxt,re.DOTALL)

            if digitalData is None :
                raise ValueError,'search digitalData Fail'

            return json.loads(digitalData.groups()[0])

        except Exception, e:
            e.message += ('function : get_DigitalData')
            raise
