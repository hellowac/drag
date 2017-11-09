# coding=utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/12/26"

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
        if status_code == 404:

            log_info = json.dumps(
                dict(time=time.time(), title=pqhtml('title').text(), url=url))

            self.logger.info(log_info)

            data = tool.get_off_shelf(
                code=status_code, message=self.cfg.SOLD_OUT, backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        # 其他错误
        if status_code != 200:

            log_info = json.dumps(
                dict(time=time.time(), title=pqhtml('title').text(), url=url))

            self.logger.info(log_info)

            data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get(
                'SCERR', 'ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        # 前期准备
        area = pqhtml('#main #primary')
        # domain = tool.get_domain(url)
        # pdata = self.get_pdata(area)

        # print area.outerHtml().encode('utf-8')
        # exit()

        # 下架
        # if True :

        # log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

        # self.logger.info(log_info)
        # data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

        # return tool.return_data(successful=False, data=data)

        detail = dict()

        # 产品ID
        productId = area('[itemprop="productID"]:first').text().replace('#','')
        detail['productId'] = productId
        detail['productSku'] = productId
        detail['productCode'] = productId

        # 品牌
        brand = area('.brand-name:first').text()
        detail['brand'] = brand

        # 名称
        detail['name'] = ' '.join([brand,area('.product-name:first').text()])

        # 价格
        price, listPrice, currency = self.get_all_price(area)
        detail['price'] = price
        detail['listPrice'] = listPrice

        # 货币，该渠道只有 欧元,美元,英镑,三种单位.
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        # 描述
        detail['descr'] = area('#pdpMain .product-detail .product-information').text()

        # 颜色
        # color = self.get_color(area)
        detail['color'] = self.cfg.DEFAULT_ONE_COLOR
        detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

        # 图片集
        imgs = [img.attr('src') for img in area('#pdpMain #product-col-2 img').items()]
        detail['img'] = imgs[0]
        detail['imgs'] = imgs

        # 规格
        detail['sizes'] = self.get_sizes(area)

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
        price_block = area('.product-content .product-price')

        ptxt = price_block('.price-sales').text().replace(',','')

        lptxt = price_block('.price-standard').text() or ptxt

        lptxt = lptxt.replace(',','')

        unit = ptxt.strip()[0]
        
        # 该渠道只有 欧元,美元,英镑,三种单位.
        if unit not in [u'$',u'€',u'£'] :
            raise Exception('currency mistake')

        price = re.search(r'(\d[\d\.]*)',ptxt).groups()[0]
        listPrice = re.search(r'(\d[\d\.]*)', lptxt).groups()[0]

        if not price or not listPrice :
            raise Exception('get price fail')

        currencys = {
            u'$':'USD',
            u'£':'GBP',
            u'€':'EUR'
        }

        return price,listPrice,currencys[unit]

    def get_sizes(self,area):
        size_block = area('.product-content #ddlSelectSize')

        sizes = []
        for ele in size_block('option[title!=""]').items() :
            name = ele.attr('title')
            inv = 1 if 'only one left' in ele.text().lower() else self.cfg.DEFAULT_STOCK_NUMBER

            sizes.append(dict(
                name=name,
                inventroy=inv,
                id=name,
                sku=name
            ))

        if not sizes :
            raise Exception('get sizes fail')

        return sizes

















