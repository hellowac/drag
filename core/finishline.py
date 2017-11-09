#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/14"

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
        # self.session.headers.update(Host='www.finishline.com')
        self.session.headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, sdch',
        'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6',
        'Cache-Control':'max-age=0',
        'Connection':'keep-alive',
        # 'Cookie':'s_cc=true; s_fid=5013E2A2C2CE7552-0DE033E989E535D6; gpv_pn=VPA; s_nr=1475721400109; s_vnum=1478313400110%26vn%3D1; s_invisit=true; s_lv=1475721400111; s_lv_s=First%20Visit; ckRfrrUrlPage1=%5B%5BB%5D%5D; clickThrough=yes; s_sq=%5B%5BB%5D%5D; __utmt=1; __utma=50624318.436263042.1475721401.1475721401.1475721401.1; __utmb=50624318.1.10.1475721401; __utmc=50624318; __utmz=50624318.1475721401.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); smtrrmkr=636113182070528854%5Ea7b04bb6-6d8b-e611-a3bc-0a913534b751%5Ea8b04bb6-6d8b-e611-a3bc-0a913534b751%5E0%5E111.199.83.10; s_vi=[CS]v1|2BFADC5F850106FB-60000106E0001E0E[CE]',
        'Host':'www.finishline.com',
        'Referer':'http://www.finishline.com/store',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'

        }


    #获取页面大概信息
    def multi(self, url):
        pass


    #获取详细信息
    def detail(self,url):
        try:
            # resp = self.session.get(url,timeout=self.cfg.REQUEST_TIME_OUT)
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
            area = pqhtml('#productDetailsWrapper')
            domain = tool.get_domain(url)
            Jtxt = pqhtml('script').text()
            # pdata = self.get_pdata(area)
            
            # print area.outerHtml()
            # exit()

            #下架
            if 'SOLD OUT' in area('#productPrice').text() or not area :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = re.search(r'FL.setup.brand = "(.*?)"',Jtxt,re.DOTALL).groups()[0]
            detail['brand'] = brand

            #名称
            detail['name'] = area('h1#title').text()

            #货币,官网固定
            currency = 'USD'
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            colors = self.get_colors(area)
            detail['color'] = colors
            detail['colorId'] = {cid:cid for cid in colors.keys()}

            #图片集
            imgs = self.get_imgs(area,pqhtml)
            detail['img'] = imgs[0] if isinstance(imgs,list) else {cid:imgArr[0] for cid,imgArr in imgs.items()}
            detail['imgs'] = imgs

            #产品ID
            productId = area('h1.title').attr('data-productitemid')
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(area)

            #键
            detail['keys'] = colors.keys()

            #描述
            detail['descr'] = area('div#productDescription').text()

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


    def get_sizes_old(self,area):
        elements = area('#productSizes .size')

        sizes = [ dict(name=sizeEle.text(),inventory=self.cfg.DEFAULT_STOCK_NUMBER if 'unavailable' not in sizeEle.attr('class') else 0 , id=sizeEle.attr('id'),sku=sizeEle.attr('data-sku')) for sizeEle in elements.items() ]

        if not sizes :
            raise ValueError,'get sizes Fail, fix this bug'

        return sizes

    #2016-12-15添加
    def get_sizes(self,area):

        sizes = dict()
        for e in area('#alternateSizes [id^="sizes_"]').items():
            colorId = e.attr('id').split('_')[-1]

            sizes_ = []
            for div in e('.size').items():

                obj = dict(
                            name=div.text(),
                            id=div.attr('data-sku'),
                            sku=div.attr('data-sku'),
                            inventory=0 if 'unavailable' in div.attr('class') else self.cfg.DEFAULT_STOCK_NUMBER
                    )
                sizes_.append(obj)

            sizes[colorId] = sizes_

        if not sizes :
            raise Exception('get sizes fail')

        return sizes


    def get_imgs_old(self,area):
        # print area.outerHtml().encode('utf-8')
        colorId = area('h1#title').attr('data-colorid')
        styleId = area('h1#title').attr('data-styleid')

        # print colorId,styleId

        link = 'http://www.finishline.com/store/api/scene7/imageset/?' + 'colorId={}&styleId={}'.format(colorId,styleId)
        
        resp = self.session.get(link, verify=False)
        # print resp.text

        jsonData = json.loads(resp.text)

        imgs = [img['url']+'?$Main$' for img in jsonData['images']]

        if not imgs :
            raise ValueError,'get Imgs Fail , fix this bug'

        return imgs

    #2016-12-15添加
    def get_imgs(self,area,pqhtml):
        alternateColors = area('#alternateColors>a')

        link = 'http://www.finishline.com/store/browse/gadgets/alternateimage.jsp'
        # link = 'http://www.finishline.com/store/browse/gadgets/alternateimage.jsp?colorID=AR3781-WHT&styleID=AR3781-WHT&productName=Men%27s+Reebok+Classic+Leather+ICE+Casual+Shoes&productItemId=prod799062&productIsShoe=true&productIsAccessory=false'
        
        params = dict(
                     productName=area('#title').text().strip().replace(' ','+'),
                     productItemId=area('#title').attr('data-productitemid'),
                     productIsShoe=pqhtml('#mainWrapper').attr('data-productisshoe'),
                     productIsAccessory=pqhtml('#mainWrapper').attr('data-productisaccessory'),
            )

        imgs = dict()
        for ele in alternateColors.items():
            productId = ele.attr('data-productid')
            sytleId = ele.attr('data-styleid')
            params.update(
                         colorID=productId,
                         styleID=sytleId)

            resp = self.session.get(link, params=params, verify=False)

            subhtml = PyQuery(resp.text)

            imgs_ = [ e.attr('data-large') for e in subhtml('#alt').items()]

            imgs[productId] = imgs_

        if not imgs :
            raise Exception('get imgs Fail')

        # print json.dumps(imgs)

        return imgs

    #2016-12-15添加
    def get_colors(self,area):
        colors = dict()

        for ele in area('#productStyleColor #altStyleColors [id^="stylecolor"]').items() :
            colorName = ele('.description').text()
            colorId = ele.attr('id').split('_')[-1]

            colors[colorId] = colorName

        if not colors :
            raise Exception('get colors fail')

        return colors


    def get_all_price(self,area):
        try:

            pblock = area('div#productPrice')
            ptxt = pblock('span.nowPrice').text() or pblock('span.maskedFullPrice') or pblock('span.fullPrice').text()

            lptxt = pblock('span.wasPrice').text() or ptxt

            price = re.search(r'(\d[\d\.]+)',ptxt).groups()[0]
            listPrice = re.search(r'(\d[\d\.]+)',lptxt).groups()[0]

            if not price or not listPrice :
                raise ValueError , 'Get price or listPrice Fail'

            return price,listPrice

        except Exception, e:
            raise

  



