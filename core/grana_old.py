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

        # pdata = self.get_pdata(area)

        detail = dict()

        # 产品ID
        productId = area(
            'form#product_addtocart_form input[name="product"]').attr('value')
        detail['productId'] = productId
        detail['productSku'] = productId
        detail['productCode'] = productId
        self.product_id = productId

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

        # 描述
        detail['descr'] = infoArea(
            '.product-info-container .product-info-tab-description').text()

        # 详细
        detail['detail'] = infoArea(
            '.product-info-container .product-info-details').text()

        # 退换货
        detail['returns'] = infoArea('.shipping-returns').text()

        # 颜色
        color = self.get_color(area)
        detail['color'] = color
        detail['colorId'] = {cid: cid for cid in color.keys()}

        # 图片集
        imgs = self.get_imgs(area)
        detail['img'] = imgs[0] if isinstance(imgs, list) else {cid: imgArr[
            0] for cid, imgArr in imgs.items()}
        detail['imgs'] = imgs

        # 规格
        detail['sizes'] = self.get_sizes(area)

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

    def get_color(self, area):
        colorArea = area('#color-attributes li .single-color-container')
        
        colors = dict()

        for ele in colorArea.items():
            colorId = ele('input').attr('value')
            colorName = ele('input').attr('class').split()[-1]
            colors[colorId] = colorName.replace('-', ' ')

        if not colors:
            raise Exception('get color fail')

        return colors

    def get_imgs(self, area):
        img_map = None

        for ele in area('script').items():
            if 'GranaObject.images = ' in ele.text():
                img_map = re.search(
                    r'GranaObject.images = (\{.*\});', ele.text()).groups()[0]
                break
        else:
            raise Exception('get imgs data fail')

        img_map = json.loads(img_map)

        if not img_map:
            raise Exception('get imgs fail')

        return img_map

    def get_sizes(self, area):
        sizes = None

        if 'waist' in area('.select-menu h3').text().lower() :
            sizes = self.get_sizes_have_waist(area)
        else :
            sizes = self.get_sizes_just_length(area)

        return sizes

    def get_sizes_have_waist(self,area):
        waist_eles = area('#waist-attributes .attribute-container ul>li')
        length_eles = area('#size-attributes .attribute-container ul>li')

        waist_map = dict()
        length_map = dict()

        # for wele,lele in zip(waist_eles.items(),length_eles.items()):           #不能用zip,长度不一样.
        for wele in waist_eles.items():
            waist_id = wele('input').attr('value')
            waist_name = wele('input').attr('data-label')
            waist_map[waist_id] = waist_name

        for lele in length_eles.items():
            length_id = lele('input').attr('value')
            length_name = lele('input').attr('data-label')
            length_map[length_id]=length_name

        for ele in area('script').items():
            if 'GranaObject.stStatus2 = ' in ele.text() :
                stock_map = re.search(
                    r'GranaObject.stStatus2 = (\{.*\});', ele.text()).groups()[0]
                break
        else :
            raise Exception('get stStatus2 fail')

        stock_map = json.loads(stock_map)['stock']

        sizes = dict()
        for cid, waistDic in stock_map.items():
            sizes_ = []
            for waist_id,lengthDic in waistDic.items():

                if isinstance(lengthDic, dict):
                    for length_id,info in lengthDic.items():
                        sizeName = 'W{waist} x L{length}'.format(waist=waist_map[waist_id],length=length_map[length_id])

                        inventory = int(float(info.get('stock_qty','0.0')))

                        obj = dict(
                            name=sizeName,
                            id=info['product_id'],
                            sku=info['product_id'],
                            inventory=inventory,
                        )
                        sizes_.append(obj)

            sizes[cid] = sizes_

        if not sizes :
            raise Exception('get sizes fail')

        return sizes

    def get_sizes_just_length(self,area):
        stock_map = None
        key_word = "GranaObject.products['{0}'] =".format(self.product_id)
        for ele in area('script').items():
            txt_ = ele.text()
            if key_word in txt_:
                stock_map = re.search(r"GranaObject\.products\['\d*'\]\s*=\s*(\{.*\});\n", txt_, re.DOTALL).groups()[0]
                break
        else:
            raise Exception('get stock and size data fail')

        stock_map = json.loads(stock_map)

        sizes = dict()

        for cid, sizeDic in stock_map.items():

            sizes_ = list()
            for sizeName, sizeInfo in sizeDic.items():
                obj = dict(
                    id=sizeInfo['size_value'],
                    sku=sizeInfo['size_value'],
                    name=sizeName,
                    inventory=int(float(sizeInfo['stock_qty']))
                )
                sizes_.append(obj)

            sizes[cid] = sizes_

        if not sizes:
            raise Exception('get sizes fail')

        return sizes
