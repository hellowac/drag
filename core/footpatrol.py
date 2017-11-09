# coding=utf-8

__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/12/21"

# 0.1 初始版

import re
import time
import demjson

from . import DragBase
from pyquery import PyQuery
from utils import tool
try:
    import simplejson as json
except ImportError, e:
    import json



class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)
        self.session.headers['Host'] = 'www.footpatrol.co.uk'
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
        # self.session.headers['Cookie'] = 'PHPSESSID=lki70nnuj7ag045d8oj3ctf0p1; ac_shop=815a4d1375ed846de975f8572ee6eafd40f1422c; li=n; SERVERID=http_68_69-2171; liveagent_oref=http://www.footpatrol.co.uk/; liveagent_ptid=b8d1ce69-200b-4f9e-8b17-991daf16dbe7; be=yes; rv=e6df6352d31ca4b45797e2ac78d82733; __atuvc=6%7C7; __atuvs=58a57aa64736f439000; mt.v=2.1156709942.1487233144119; _ga=GA1.3.258859120.1487233155; sc.ASP.NET_SESSIONID=cvn0kaonlxnp4g2w5r05nmr4; sc.Status=4; liveagent_sid=6606efb9-7caf-4b29-87f7-12b70a401a7f; liveagent_vc=9; akavpau_VP1=1487240170~id=fa3f0358b9a57407b221cdbe8c0b313d'
        self.session.headers['Cookie'] = 'SERVERID=http_68_69-2171; ak_bmsc=18B6AF712016E324F55E6EE1136D6C22B83257A6EC270000C16BA658C0A2262B~pl8YLGTsxLsR0Q44FD29c2DQbH45AvgatRgjUZiVgj3A7A2CWqPFvjTeBl+P2FaJG2ZtidcmAsrNY67Jh7WySI2WYveGXf+CfBRJBEXiWA+hBlt9bxf4fEx6WG37/cV7gEgY8YhjLTl462vvQzfyou2ClXeKYejq1A3H4kIMhkd5iMQP/3m1WHt6SZct2P9Qh6utjRI+OjHGVgM2AA1zlGNXWv9a24EWj4l7rFmkJi+K4=; _ga=GA1.3.2109996279.1487301570; _gat=1; akavpau_VP1=1487301871~id=1386f5ee7c049897134cfd644a2cd4ff'

    # 获取页面大概信息
    def multi(self, url):
        pass

    # 获取详细信息
    def detail(self, url):
        resp = self.session.get(url, verify=False)

        status_code = resp.status_code
        pqhtml = PyQuery(resp.text or 'nothing')

        is_ok,not_ok_data = self.is_ok_status_code(status_code, pqhtml, url, resp)

        if not is_ok :
            return not_ok_data

        # 前期准备
        area = pqhtml('[role="main"]')
        # domain = tool.get_domain(url)
        # pdata = self.get_pdata(area)

        prod_data = self.get_prod_data(pqhtml)

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
        productId = area('input[name="product_id"]').attr('value') or prod_data['plu']
        detail['productId'] = productId
        detail['productSku'] = productId
        detail['productCode'] = productId

        # 品牌
        brand = prod_data['brand']
        detail['brand'] = brand

        # 名称
        detail['name'] = PyQuery(prod_data['description']).text()

        # 货币
        currency = prod_data['currency']
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        # 价格
        price = prod_data['unitPrice']
        listPrice = self.get_list_price(area) or price
        detail['price'] = price
        detail['listPrice'] = listPrice

        # 描述
        detail['descr'] = area('.fp-accordian-content').text()

        # 退换货
        detail['returns'] = area('.fp-accordian-contents:eq(1)').text()

        # 颜色
        # color = self.get_color(area)
        detail['color'] = self.cfg.DEFAULT_ONE_COLOR
        detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

        # 图片集
        imgs = [img.attr('data-overlay') for img in pqhtml('ul.fp-product-thumbs>li>img').items()]

        detail['img'] = area('.fp-product-image a').attr('href')
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

    def get_prod_data(self,pqhtml):
        head = pqhtml('head')

        prodData = None

        for ele in head('script').items() :
            if 'var dataObject = ' in ele.text() :
                prodData = re.search(r'var dataObject = (\{.*\});',ele.text(),re.DOTALL).groups()[0]
                break
        else :
            raise Exception('get prod data fail')

        prodData = demjson.decode(prodData)

        return prodData

    def get_list_price(self,area):
        priceBlock = area('.product-heading')

        priceTxt = priceBlock('.price-was').text()

        if priceTxt :
            return re.search(r'(\d[\d\.]*)', priceTxt).groups()[0]

        return None

    def get_sizes(self,area):
        """获取sizes

        该渠道能获取到的size都是有库存的,至少一个.但不能获取详细库存.

        Args:
            area:商品块.PyQuery对象.

        Returns:
            包含size实例的集合列表.

        Raises:
            pass
        """
        attributes = area('.attribute_container .attribute_size select option[value!=""]')

        sizes = []

        for option in attributes.items() :
            size_name = option.text()
            size_id = option.attr('value')

            obj = dict(
                name=size_name,
                id=size_id,
                sku=size_id,
                inventory=self.cfg.DEFAULT_STOCK_NUMBER
            )

            sizes.append(obj)

        if not sizes :
            raise Exception('get sizes fail')

        return sizes














