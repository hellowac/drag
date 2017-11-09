# coding=utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/12/28"

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
        area = pqhtml('section.pdp-main')

        # print area.outerHtml().encode('utf-8')
        # exit()

        # 下架
        tag_txt = area('.product-right .product-tag').text() or ''
        if not area or 'sold out' in tag_txt.lower() or 'back in stock' in tag_txt.lower():

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)
            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        detail = dict()

        # 产品ID
        productId = self.get_product_id(pqhtml)
        detail['productId'] = productId
        detail['productSku'] = productId
        detail['productCode'] = productId

        # 品牌
        brand = 'MVMT'
        detail['brand'] = brand

        # 名称
        detail['name'] = area('[itemprop="name"]:first').text()

        # 货币
        currency = pqhtml('meta[itemprop="priceCurrency"]').attr('content')
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        # 价格
        price, listPrice = self.get_all_price(area)
        detail['price'] = price
        detail['listPrice'] = listPrice

        # 描述
        detail['descr'] = pqhtml('section.watch-pdp-details').text()

        # 颜色
        # color = self.get_color(area)
        detail['color'] = self.cfg.DEFAULT_ONE_COLOR
        detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

        # 图片集
        imgs = [ 'http:'+img.attr('src') for img in area('.product-left .product-slider img').items()]
        detail['img'] = imgs[0]
        detail['imgs'] = imgs

        # 规格
        detail['sizes'] = [dict(
            name=self.cfg.DEFAULT_ONE_SIZE,
            id=self.cfg.DEFAULT_SIZE_SKU,
            sku=self.cfg.DEFAULT_SIZE_SKU,
            inventory=self.cfg.DEFAULT_STOCK_NUMBER
        )]

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

    def get_all_price(self,area):
        price_block = area('.price-wrapper')

        ptxt = price_block('.sale-price .money').text() or price_block('.price .money').text()
        lptxt = price_block('.compare-price .money').text() or ptxt

        if not ptxt or not lptxt :
            raise Exception('get price text fail')

        price = re.search(r'(\d[\d\.]*)', ptxt).groups()[0]
        listPrice = re.search(r'(\d[\d\.]*)', lptxt).groups()[0]

        if not price or not listPrice :
            raise Exception('get price fail')

        return price,listPrice

    def get_product_id(self, pqhtml):

        meta = ''
        for script in pqhtml('script').items():
            if 'var meta' in script.text():
                meta = re.search(r'var meta\s*=\s*(\{.*\});', script.text()).groups()[0]
                break
        else:
            raise Exception('get product id fail')

        meta = json.loads(meta)

        return meta['product']['id']











