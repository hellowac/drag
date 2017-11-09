# coding=utf-8
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
        area = pqhtml('.product-detail-information')
        domain = tool.get_domain(url)
        pdata = self.get_pdata(area)

        # exit()

        # 下架
        # if not area :

        #     log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

        #     self.logger.info(log_info)
        #     data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

        #     return tool.return_data(successful=False, data=data)

        detail = dict()

        # 产品ID
        productId = area('.product-detail-selection-sku').text()
        detail['productId'] = productId
        detail['productSku'] = productId
        detail['productCode'] = productId

        # 品牌
        brand = None
        detail['brand'] = brand

        # 名称
        detail['name'] = area('.J_title_name').text()

        # 货币
        currency = pqhtml('a#select_currency').text().split()[0]
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        # 价格
        price, listPrice = self.get_all_price(area)
        detail['price'] = price
        detail['listPrice'] = listPrice

        # 描述
        detail['descr'] = area('#product-description-tab').text()

        # 详细
        detail['detail'] = area('#product-description-tab').text()

        # 退换货
        detail['returns'] = area('.product-directions').text()

        # 颜色
        # color = self.get_color(area)
        detail['color'] = self.cfg.DEFAULT_ONE_COLOR
        detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

        # 图片集
        imgs = [a.attr('href') for a in pqhtml(
            '.product-detail-preview .toolbar>li>a').items()]
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
