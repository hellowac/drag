#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/13"

#0.1 初始版
from collections import defaultdict
from . import DragBase
from xml.dom import minidom
from pyquery import PyQuery
from utils import tool
from exception import NotMustKeyError
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

            self.url=url

            status_code = resp.status_code

            self.status_code = status_code

            self.fst_resp = resp

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
            pdata = self.get_pdata(pqhtml)

            #colorsList节点不存在，商品售完
            if 'colorsList' not in pdata['productDetails']:

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)
                
            detail = dict()

            # 产品ID
            productId = pdata['productDetails']['productCode']
            detail['productId'] = productId
            detail['productSku'] = productId
            detail['productCode'] = productId
            self.product_code = productId

            # 品牌
            brand = pdata['seoProperties']['title'].split('|')[-1]
            detail['brand'] = brand

            # 名称
            detail['name'] = '{0} {1}'.format(brand, pdata['productDetails']['productName'])

            # 货币
            if pdata['countryCode'] != 'us':
                raise Exception('check currency fail')

            currency = 'USD'
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            # 价格
            detail['price'] = pdata['productDetails']['listPrice']['amount']  # 不同颜色不同价格，先复制 list_price
            detail['listPrice'] = pdata['productDetails']['listPrice']['amount']

            # 描述
            detail['descr'] = ' '.join(pdata['productDetails']['productDescriptionTech'])  # 这里是一个字符串列表.

            # 详细
            detail['detail'] = detail['descr']

            # 退换货
            detail['returns'] = ''

            # 多颜色，多价格, 图片集
            price, color, img, imgs = self.get_color_and_price(pdata, pqhtml)

            detail['price'] = price
            detail['color'] = color  # 字典, key为颜色ID，value为颜色名称
            detail['colorId'] = {cid:cid for cid in color.keys()}
            detail['img'] = img
            detail['imgs'] = imgs
            detail['keys'] = color.keys()  # 根据颜色ID去区分不同的商品

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

        except Exception:
            raise

    def get_pdata(self, pqhtml):
        """ 获取官网商品详细json"""
        try:
            pdata = re.search(r'var pdpJSON = (\{.*\});\n', pqhtml.text()).groups()[0]
            pdata = json.loads(pdata)
        except Exception:
            raise Exception('get pdata fail')
                
        return pdata

    def get_color_and_price(self, pdata, pqhtml):
        """ 从详细json中提取颜色和价格信息"""
        colors_list = pdata['productDetails']['colorsList']
        img_api = 'https://i.s-jcrewfactory.com/is/image/jcrew/{0}_{1}?fmt=jpeg&qlt=90,0&resMode=sharp&op_usm=.1,0,0,0&wid=1200&hei=1200'

        price = dict()
        color = dict()
        img = dict()
        imgs = dict()
        for item in colors_list:
            for colour in item['colors']:
                cid = colour['code']
                cname = colour['name']

                price[cid] = item['price']['amount']
                color[cid] = cname
                img_ = img_api.format(self.product_code, cid)
                img[cid] = img_
                imgs[cid] = [img_]

        return price, color, img, imgs

    def get_sizes(self, pdata):
        """ 从商品信息中获取尺码信息"""
        stock_api = 'https://factory.jcrew.com/data/v1/us/products/inventory/{0}'.format(self.product_code)
        try:
            stock_info = self.session.get(stock_api).json()['inventory']
        except Exception:
            raise Exception('get stock info fail')

        skus = pdata['productDetails']['skus']
        sizes = defaultdict(list)  # 默认值为列表的字典类型
        for code, sku in skus.items():
            cid = sku['colorCode']
            price = sku['price']['amount']
            list_price = sku['listPrice']['amount']
            size_name = sku['size']
            size_id = size_name   # 原库中就用的name，要兼容以前的商品. sku['skuId'] , 2017-06-13 18:28:07

            size_inventory = stock_info.get(code, {}).get('quantity', 0)
            retail_only = stock_info.get(code, {}).get('retailOnly', False)
            size_inventory = 0 if retail_only else size_inventory  # 是否仅限零售

            size_obj = dict(name=size_name, id=size_id, sku=size_id, inventory=size_inventory, price=price, listPrice=list_price)
            sizes[cid].append(size_obj)

        return sizes

