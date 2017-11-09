# coding=utf-8

from __future__ import unicode_literals

__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2017/01/20"

# 0.1 初始版
import re
import time
from pyquery import PyQuery
try:
    import simplejson as json
except ImportError, e:
    import json
    
from . import DragBase
from utils import tool


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)

    # 获取页面大概信息
    def multi(self, url):
        pass

    # 获取详细信息
    def detail(self, url):
        resp = self.session.get(url, verify=False)

        status_code = resp.status_code
        pqhtml = PyQuery(resp.text or 'nothing')

        # 下架
        is_ok,data = self.is_ok_status_code(status_code, pqhtml, url, resp)

        if not is_ok :
            return data

        # 前期准备
        area = pqhtml('#contentArea')
        domain = tool.get_domain(url)
        # pdata = self.get_pdata(area)
        productId = area('form input[name="prodCode"]').attr('value')

        pdata = self.get_pdata(productId)

        # print pdata

        # print area.outerHtml().encode('utf-8')

        # exit()

        # 下架
        if not pdata and not area('#divSelectOpt input') :

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)
            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        detail = dict()

        # 产品ID
        detail['productId'] = productId
        detail['productSku'] = productId
        detail['productCode'] = productId

        # 品牌
        brand = area('.detailInfo .infoTable .titleWrap a:first').text()
        detail['brand'] = brand

        # 名称
        detail['name'] = area('.detailInfo .infoTable .titleWrap').text()

        # 价格
        currency, price, listPrice = self.get_all_price(area)
        detail['price'] = price
        detail['listPrice'] = listPrice

        # 货币,取固定的美元价格
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        # 描述
        detail['descr'] = area('.infoTable .optTable_1').text() or u'没有获取到描述'

        # 颜色
        # color = self.get_color(area)
        detail['color'] = self.cfg.DEFAULT_ONE_COLOR
        detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

        # 图片集
        imgs = [ 'http://www.sheisback.com'+img.attr('src') for img in area('.detailArea img').items()]
        detail['img'] = 'http://www.sheisback.com' + area('.detailImg img:first').attr('data-zoom-image')
        detail['imgs'] = imgs

        # 规格
        detail['sizes'] = self.get_sizes(pdata)

        # HTTP状态码
        detail['status_code'] = status_code

        # 状态
        detail['status'] = self.cfg.STATUS_SALE

        # 返回链接
        detail['backUrl'] = resp.url

        # 返回的IP和端口
        if resp.raw._original_response.peer:
            detail['ip_port'] = ':'.join(
                map(lambda x: str(x), resp.raw._original_response.peer))

        log_info = json.dumps(dict(time=time.time(),
                                   productId=detail['productId'],
                                   name=detail['name'],
                                   currency=detail['currency'],
                                   price=detail['price'],
                                   listPrice=detail['listPrice'],
                                   url=url))

        self.logger.info(log_info)

        return tool.return_data(successful=True, data=detail)

    def get_pdata(self,productId):
        link = 'http://www.sheisback.com/cn/'
        params = dict(
            menuType='product',
            mode='json',
            act='prodOptAttr',
            prodCode=productId
        )

        response = self.session.get(link,params=params, verify=False)

        return response.json()

    def get_all_price(self,area):
        priceBlock = area('.detailInfo .infoTable')

        # print priceBlock.outerHtml().encode('utf-8')

        # exit()

        ptxt = priceBlock('.realPriceRow').text()
        lptxt = priceBlock('.priceOrg').text() or ptxt

        for tr in priceBlock('tr').items():
            if '特别折扣价' in tr.text():
                ptxt = tr('.priceOrange').text()

        ptxt = ptxt.replace('￥', 'CNY')
        lptxt = lptxt.replace('￥', 'CNY')

        ptxt = ptxt.replace(',','').encode('utf-8')
        lptxt = lptxt.replace(',','').encode('utf-8')

        price = re.search(r'CNY\s*(\d[\d\.]*)', ptxt).groups()[0]

        listPrice = re.search(r'CNY\s*(\d[\d\.]*)', lptxt).groups()[0]

        listPrice = price if price > listPrice else listPrice

        if not price or not listPrice :
            raise Exception('get Price fail')

        #取固定美元价格
        return 'CNY',price,listPrice

    def get_sizes(self,pdata):
        # print json.dumps(pdata)

        if pdata and not isinstance(pdata, dict) :
            raise Exception('pdata type error')

        elif pdata :

            sizes = []
            for sizeId,info in pdata.iteritems():
                if info['PO_NAME1'] not in ['SIZE',u'尺寸',u'尺码','Size'] :
                    raise Exception('size name not equal SIZE')

                sizeName = info['POA_ATTR1']
                # sizePrice = info['POA_SALE_PRICE_USD']  # 美元.
                sizePrice = info['POA_SALE_PRICE']  # 人民币...
                inventory = info['POA_STOCK_QTY']

                sizes.append(dict(
                    id=sizeId,
                    sku=sizeId,
                    name=sizeName,
                    price=sizePrice,
                    inventory=inventory,
                ))
        else :
            # one size

            sizes = [dict(
                id=self.cfg.DEFAULT_SIZE_SKU,
                sku=self.cfg.DEFAULT_SIZE_SKU,
                name=self.cfg.DEFAULT_ONE_SIZE,
                inventory=self.cfg.DEFAULT_STOCK_NUMBER
                )]

        if not sizes:
            raise Exception('get sizes fail')

        return sizes




















