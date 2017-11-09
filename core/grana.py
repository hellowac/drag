#!/usr/bin/python
# coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/08/12"

# 0.1 初始版
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
        area = pqhtml('.product-header-container')
        infoArea = pqhtml('.product-info')

        # print area.outerHtml().encode('utf-8')
        # exit()

        # 下架
        if not area:

            log_info = json.dumps(
                dict(time=time.time(), title=pqhtml('title').text(), url=url))

            self.logger.info(log_info)
            data = tool.get_off_shelf(
                code=status_code, message=self.cfg.SOLD_OUT, backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)


        detail = dict()

        # 产品ID
        productId = area(
            'form#product_addtocart_form input[name="product"]').attr('value')
        detail['productId'] = productId
        detail['productSku'] = productId
        detail['productCode'] = productId
        self.product_id = productId

        pdata = self.get_pdata(area)

        # 品牌
        brand = 'Grana'
        detail['brand'] = brand

        # 名称
        detail['name'] = area('.product-price-block h2').text()

        # 货币
        currency = pqhtml('meta[property="product:price:currency"]').attr('content')
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        # 价格
        price = pqhtml('meta[property="product:price:amount"]').attr('content')
        oldPriceTxt = area('.price-margin span[id^="old-price"]').text()
        listPrice = re.search(
            r'(\d[\d\.]*)', oldPriceTxt).groups()[0] if oldPriceTxt else price

        detail['price'] = price
        detail['listPrice'] = listPrice

        infoArea('script').empty()

        # 描述
        detail['descr'] = infoArea(
            '.product-info-container .product-info-tab-description').text()

        # 详细
        detail['detail'] = infoArea(
            '.product-info-container .product-info-inner.product-info-details li').text()

        # 退换货
        detail['returns'] = infoArea('.shipping-returns').text()

        # 获取 图片，尺码，信息

        color, img, imgs, sizes = self.get_sizes_imgs(pdata)

        # 图片集
        detail['img'] = img
        detail['imgs'] = imgs

        # 颜色
        detail['color'] = color
        detail['colorId'] = {cid: cid for cid in color.keys()}

        # 规格
        detail['sizes'] = sizes

        # keys
        detail['keys'] = color.keys()

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

    def get_sizes_imgs(self, pdata):

        # print json.dumps(pdata)

        color_attr = None
        has_waist = False

        for attr_id, attr in pdata['attributes'].items():
            if attr['code'] in ['color', 'shirt_color']:
                color_attr = attr
            elif attr['code'] == 'waist':
                has_waist = True

        if not color_attr :
            raise ValueError('get color data fail')

        colors_dict = {}
        imgs_dict = {}
        img_dict = {}
        color_ids = {}

        for option in color_attr['options']:
            color_id = option['id']
            color_name = option['label']
            pids = option['products']

            colors_dict[color_id] = color_name
            color_ids[color_id] = pids

        product_imgs = pdata['images']
        product_sizes = pdata['productInfo']

        # 获取图片
        for color_id, cids in color_ids.items():
            main_img = ''
            for cid in cids :
                imgs_ = product_imgs[cid]
                imgs = [img['img'] for img in imgs_]
                main_img = [img['img'] for img in imgs_ if img['isMain']][0] if not main_img else main_img
            imgs_dict[color_id] = imgs
            img_dict[color_id] =  main_img # 只能获取一张主图.

        # 获取尺码，无waist.
        if has_waist:
            sizes_dict = self.get_sizes_has_waist(color_ids, product_sizes)
        else:
            sizes_dict = self.get_sizes_no_waist(color_ids, product_sizes)
        

        return colors_dict, img_dict, imgs_dict, sizes_dict

    def get_sizes_has_waist(self, color_ids, product_sizes):
        """ 获取有宽度和长度的尺码，如裤子. """
        sizes_dict = {}
        for color_id in color_ids.keys():
            sizes = product_sizes[color_id]

            size_arr = []
            for waist, length_list in sizes.items():
                for length_info in length_list:
                    length = length_info['length']
                    obj = dict(name='W{0} x L{1}'.format(waist, length),
                               inventory=length_info['stock_qty'],
                               id=length_info['simple_product_id'],
                               sku=length_info['simple_product_id'])
                    size_arr.append(obj)

            sizes_dict[color_id] = size_arr

        if not sizes_dict :
            raise ValueError('get sizes fail')

        return sizes_dict

    def get_sizes_no_waist(self, color_ids, product_sizes):
        """ 获取没有宽度和长度的尺码，如上衣. """
        sizes_dict = {}
        for color_id in color_ids.keys():
            sizes = product_sizes[color_id]

            size_arr = []
            for size_name, size_info in sizes.items():
                obj = dict(name=size_name,
                           inventory=size_info['stock_qty'],
                           id=size_info['simple_product_id'],
                           sku=size_info['simple_product_id'])
                size_arr.append(obj)

            sizes_dict[color_id] = size_arr

        if not sizes_dict :
            raise ValueError('get sizes fail')

        return sizes_dict

    def get_pdata(self,area):
        data = None
        key_word = "GranaObject.products['{0}'] =".format(self.product_id)
        for ele in area('script').items():
            txt_ = ele.text()
            if key_word in txt_:
                data = re.search(r"GranaObject\.products\['\d*'\]\s*=\s*(\{.*\});\n", txt_, re.DOTALL).groups()[0]
                break
        else:
            raise Exception('get stock and size data fail')

        data = json.loads(data)

        if not data:
            raise Exception('get product data fail')

        return data
