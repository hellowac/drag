#!/usr/bin/python
# coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/04"

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

        # 前期准备:
        # Jtxt = pqhtml('script').text()
        pdata = self.get_pdata(pqhtml)
        area = pqhtml('.productDetailSummary')
        pinfo = pqhtml('#productInfo')
        imgPath = url.split('/')[3]

        # print area.outerHtml()
        # print json.dumps(pdata)
        # exit()

        # 下架
        if not pdata:

            log_info = json.dumps(
                dict(time=time.time(), title=pqhtml('title').text(), url=url))

            self.logger.info(log_info)

            data = tool.get_off_shelf(
                code=status_code, message=self.cfg.SOLD_OUT, backUrl=resp.url, html=pqhtml.outerHtml())
            return tool.return_data(successful=False, data=data)

        detail = dict()

        # 名称
        detail['name'] = pqhtml('.productName').text()

        # 品牌
        detail['brand'] = pqhtml('.productName a').text()

        # 货币
        currency = area('span[itemprop="priceCurrency"]').text()
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        # 价格
        price, listPrice = self.get_all_price(area)
        detail['price'] = price
        detail['listPrice'] = listPrice

        # 图片集
        img, imgs = self.get_imgs(area, imgPath)
        detail['img'] = img
        detail['imgs'] = imgs

        # 视频
        if len(area('.MagicScroll .productVideo')) > 0:
            detail['video'] = area(
                '.MagicScroll a.productVideo').attr('data-video-url')

        # 颜色
        colors, sizes = self.get_colors_sizes(area, pdata)
        detail['color'] = colors
        detail['sizes'] = sizes

        detail['keys'] = colors.keys()

        detail['colorId'] = dict([(key, key) for key in colors.keys()])

        # 产品ID
        productId = area('input#baseNo').attr('value')
        detail['productId'] = productId

        # 描述
        detail['descr'] = pinfo('#overview').text()

        # 详情
        detail['detail'] = pinfo('#specs').text()

        # HTTP状态码
        detail['status_code'] = status_code

        # 状态
        detail['status'] = self.cfg.STATUS_SALE

        # 返回链接
        detail['backUrl'] = url

        log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                              'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

        self.logger.info(log_info)

        return tool.return_data(successful=True, data=detail)

    def get_imgs(self, area, imgPath):
        # defaultImgs = [ img.attr('href') for img in area('a.altImage').items() ]
        # defaultImg = area('.primaryImageContainer a:first').attr('href')

        colors = [ele.attr('value') for ele in area(
            '#selectedProperty1 option[value!=""]').items()]

        imgs = dict([(cid, ['http://i.stpost.com/%s_%s~1500.5.jpg' %
                            (imgPath, cid)]) for cid in colors])

        img = dict([(cid, 'http://i.stpost.com/%s_%s~1500.5.jpg' %
                     (imgPath, cid)) for cid in colors])

        return img, imgs

    def get_colors_sizes(self, area, pdata):
        # 颜色
        colors = dict([(ele.attr('value'), ele.text()) for ele in area(
            '#selectedProperty1 option[value!=""]').items()])

        # size
        sizeId2Name = dict([(ele.attr('value'), ele.text()) for ele in area(
            'select#selectedProperty2 option[value!=""]').items()])

        # 宽度
        widths = [ele.attr('value') for ele in area(
            '#selectedProperty3 option[value!=""]').items()]
        needWidth = len(widths) > 1

        sizes = dict()
        for obj in pdata:
            colorId = obj['property1']
            sizeId = obj['property2']
            widthId = obj['property3']

            msg = obj['availabilityCss']
            price = obj['finalPromoPrice']

            # 库存
            if 'In Stock' == msg:
                inv = self.cfg.DEFAULT_STOCK_NUMBER
            elif 'Only' in msg:
                inv = re.search(r'Only (\d{1}) left', msg).groups()[0]
            else:
                inv = 0

            # size名称,如果宽度数量大于1.
            if widthId and needWidth:
                sizeName = (widthId + ' ' + sizeId2Name[sizeId])
            else:
                sizeName = sizeId2Name[sizeId]

            # size 标识,这个标识亘古不变,依赖他更新库.
            if needWidth:
                sizeSku = widthId + sizeId
            else:
                sizeSku = sizeId

            obj = dict(name=sizeName, inventory=inv,
                       sku=sizeSku, price=price[1:])

            if colorId in sizes:
                sizes[colorId].append(obj)
            else:
                sizes[colorId] = [obj]

        return colors, sizes

    def get_all_price(self, area):
        price = area('span[itemprop="price"]').text().replace(',', '')
        ptxt = area('.retailPrice').text().replace(',', '')

        if ptxt:
            listPrice = re.search(r'(\d[\d\.]+)', ptxt).groups()[0]
        else:
            listPrice = price

        return price, listPrice

    def get_pdata(self, pqhtml):
        taffy = pqhtml('#taffyDb script').text()

        taffy = re.search(
            r'var skus = new TAFFY\(.*?(\[.*?\])\s*\);$', taffy, re.DOTALL).groups()[0]

        # property1 = 'property1'
        # property2 = 'property2'
        # property3 = 'property3'
        # availabilityMsg = 'availabilityMsg'
        # availabilityCss = 'availabilityCss'
        # expectedDeliveryDate = 'expectedDeliveryDate'
        # finalPromoPrice = 'finalPromoPrice'
        # isComingSoon = 'isComingSoon'
        # priceLabel = 'priceLabel'
        # qtyLimit = 'qtyLimit'
        # limitMessage = 'limitMessage'

        arr = None
        exec('arr =' + taffy)

        return arr
