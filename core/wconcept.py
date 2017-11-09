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
        area = pqhtml('.goodsDetail')
        # domain = tool.get_domain(url)

        # print area.outer_html().encode('utf-8')

        # exit()

        # 下架
        if u'已售罄' in unicode(area('a[data-target="#choose-form"]').text()) :

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)
            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        detail = dict()

        # 品牌
        brand = area('.productOption .productDescrip #brandLink').text()
        detail['brand'] = brand

        # 名称
        detail['name'] = area('.productOption .productDescrip .product-name').text()

        # 货币
        currency = 'CNY'
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        # 价格
        productId, price, listPrice = self.get_all_price(area)
        detail['price'] = price
        detail['listPrice'] = listPrice

        # 产品ID
        detail['productId'] = productId
        detail['productSku'] = productId
        detail['productCode'] = productId

        # 描述
        detail['descr'] = pqhtml('.clearfloat  #productDetail #productAdditionalData').text()

        # 详细
        detail['detail'] = pqhtml('.clearfloat #productDetail #productAdditionalData').text()

        # 退换货
        detail['returns'] = area('.deliveryWay').text()

        # 图片集
        detailImgs = [img.attr('data-pagespeed-lazy-src') or img.attr('src') for img in pqhtml('#productDescription img').items()]
        
        imgs = [img.attr('data-pagespeed-lazy-src') or img.attr('src') for img in area('.productShow .imgShow .item img').items()]
        imgs.extend(detailImgs)

        img = area('.productShow .bigimgShow img:first')

        detail['img'] = img.attr('data-pagespeed-lazy-src') or img.attr('src')
        detail['imgs'] = imgs

        colors,sizes = self.get_all_colors_and_sizes(area)

        # 颜色
        detail['color'] = colors
        detail['colorId'] = {cid:cid for cid in colors.keys()}

        # 规格
        detail['sizes'] = sizes

        # 钥匙
        detail['keys'] = colors.keys()

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
        for script in area('script').items():
            if 'optionsPrice' in script.text():
                optionsPriceTxt = script.text()
                break
        else:
            raise Exception('get price fail')

        optionsPrice = re.search(r'var optionsPrice\s*=\s*new Product\.OptionsPrice\((.*)\);', optionsPriceTxt).groups()[0]
        optionsPrice = json.loads(optionsPrice)

        price = optionsPrice['productPrice']
        oldPrice = optionsPrice['productOldPrice']
        productId = optionsPrice['productId']

        if not price or not oldPrice :
            raise Exception('get price or oldPrice fail')

        return productId,price,oldPrice

    def get_all_colors_and_sizes(self,area):
        for script in area('script').items():
            if 'simple_products' in script.text():
                simple_productsTxt = script.text()
                break
        else :
            raise Exception('get simple_products fial')

        simple_products = re.search(r'var simple_products\s*=\s*(\[.*\}\]);\s*var', simple_productsTxt).groups()[0]
        simple_products = json.loads(simple_products)

        sizes = {}
        colors = {}

        for product in simple_products:
            price = product['price']
            inventory = product['qty']

            for attribute in product['attributes']:

                if attribute['attribute_code'] == 'color':
                    colorName = attribute['option_label']
                    colorId = attribute['option_id']

                elif attribute['attribute_code'] == 'size':
                    sizeName = attribute['option_label']
                    sizeId = attribute['option_id']

            size = dict(name=sizeName,
                id=sizeId,
                sku=sizeId,
                price=price,
                inventory=inventory
            )

            if colorId not in sizes :
                sizes[colorId] = [size]
            else :
                sizes[colorId].append(size)

            if colorId not in colors :
                colors[colorId] = colorName

        if not sizes or not colors :
            raise Exception('get sizes or colors fail')

        return colors,sizes













