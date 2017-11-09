#!/usr/bin/python
# coding=utf-8
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
import requests
from requests.cookies import RequestsCookieJar
# from pyquery.cssselectpatch import cssselect_xpath as xpath


class Drag(DragBase, object):

    def __init__(self, cfg):

        super(Drag, self).__init__(cfg)

        self._retry = 0
        self.cookies = None


    #获取页面大概信息
    def multi(self, url):
        pass


    #获取详细信息
    def detail(self,url):
        try:
            resp = requests.get(url, verify=False)

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
            area = pqhtml('#bd .grid')
            # domain = tool.get_domain(url)
            pdata = self.get_pdata(pqhtml)

            # print area.outerHtml().encode('utf-8')
            
            #下架
            if not len(area('.p-buy #addCart .buynow')) :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            #产品应该只有一个
            if len(pdata['prods']) != 1 :
                raise ValueError('yintai product data length great than 1')

            detail = dict()

            #品牌
            brand = area('h4.y-pro-cooper-name').text()
            detail['brand'] = brand

            #名称
            detail['name'] = pdata['prods'][0]['name']

            #货币
            currency = 'CNY'
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            price = pdata['prods'][0]['price']

            if u'直降' in area('#Y_ProBen').text() :
                self.session.headers['Referer'] = url
                self.session.headers['X-Requested-With'] = 'XMLHttpRequest'
                # self.session.headers['Origin'] = 'http://item.yintai.com'
                self.session.headers['Origin'] = url

                # subArea = PyQuery(self.session.post(url,data=dict()).text)
                subArea = PyQuery(requests.post(url,data=dict(),headers=self.session.headers,cookies=resp.cookies).text)

                price = re.search(r'(\d[\d\.]*)',subArea('.marketPriceNum .yt-num').text()).groups()[0]
                price = price + subArea('.marketPriceNum .yt-num em').text()


            #价格，该业务逻辑后边删除
            detail['price'] = float(price)
            detail['listPrice'] = pdata['prods'][0]['mPrice']

            # print area('.productInfo .s-s-color').next()('a[href="Javascript:void(0);"]').outerHtml().encode('utf-8')
            # print area('.productInfo .s-s-color').next()('.selected a').text()

            #颜色
            # color = self.get_color(area)
            color = area('.productInfo .s-s-color').next()('a[href="Javascript:void(0);"]').text()
            color = color or area('.productInfo .s-s-color').next()('.selected a').text()               #2016-12-15添加
            detail['color'] = color
            detail['colorId'] = pdata['prods'][0]['colorID']

            #图片集
            imgs = self.get_imgs(area)
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #产品ID
            productId = pdata['prods'][0]['sku']
            detail['productId'] = productId

            #规格
            detail['sizes'] = self.get_sizes(area)

            #描述
            detail['descr'] = area('.yp-con-desc').text()

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url

            self.session.cookies = RequestsCookieJar()
            self.session.headers = tool.get_one_header()

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)


            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            if 'get YinTai_TagData Fail' in str(e) and self._retry < 10 :
                self._retry += 1
                return self.detail(url)
            elif self._retry >= 10 :
                raise ValueError('yintai retry five times ,{0}'.format(str(e)))
            else :
                raise


    def get_pdata(self,pqhtml):
        
        for ele in pqhtml('script[type="text/javascript"]').items() :
            if 'YinTai_TagData' in ele.text() :

                data = ele.text().replace('var YinTai_TagData= ','')

                return json.loads(data)

        raise ValueError('get YinTai_TagData Fail,html:{0}'.format(pqhtml.outerHtml()))


    def get_imgs(self,area):
        elements = area('.p-photos ul li a')

        imgs = [ re.search(r'bigImage:\'(.*?)\'',ele.attr('rel')).groups()[0] for ele in elements.items() ]

        if not imgs :
            raise ValueError('get Imgs Fail')

        def prefix_img(s):
            if not s :
                raise Exception('img link is null')
                
            if s.startswith('//'):
                return 'http:'+s
            return s

        #添加图片头验证
        imgs = map(prefix_img, imgs)

        return imgs


    def get_sizes(self,area):

        # print area.outerHtml().encode('utf-8')

        elements = area('.selSize dd .item')

        # print elements.outerHtml().encode('utf-8')

        sizes = list()

        for ele in area('.selSize dd .item').items() :

            inv = 0  if 'soldOut' in ele.attr('class') or 'javascript:void(0);' in ele('a').attr('href') else self.cfg.DEFAULT_STOCK_NUMBER

            sku = ele('a').attr('rel') or ele('a').attr('title') or ele('a').text()

            sku = sku[:-1] if sku and sku[-1]=='$' else sku

            obj = dict(name=ele('a').text(),sku=sku,id=sku,inventory=inv)
            
            sizes.append(obj)

        if not sizes :
            elements = area('.selSize dd .item a')

            if len(elements) !=1 :
                raise ValueError('not sku attribute elements great than 1')

            for ele in elements.items() :
                obj = dict(name=ele.text(),
                            sku=ele.attr('rel') or self.cfg.DEFAULT_SIZE_SKU,
                            id=ele.attr('rel') or self.cfg.DEFAULT_SIZE_SKU,
                            inventory=self.cfg.DEFAULT_STOCK_NUMBER if 'javascript:void(0);' not in ele.attr('href') else 0 )
                sizes.append(obj)

        if not sizes :
            raise ValueError('get sizes Fail')

        #one color 和 one size 下判断有没有库存
        if len(sizes) == 1 and sizes[0]['inventory'] == 0 and len(area('.p-buy #addCart .buynow')) :
            sizes[0]['inventory'] = self.cfg.DEFAULT_STOCK_NUMBER

        return sizes

    

