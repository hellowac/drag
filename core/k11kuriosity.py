# coding:utf-8
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
        add_tocart = pqhtml('#buy')

        # 下架
        if status_code == 404 or not add_tocart:

            log_info = json.dumps(
                dict(time=time.time(), title=pqhtml('title').text(), url=url))

            self.logger.info(log_info)

            data = tool.get_off_shelf(
                code=status_code, message=self.cfg.SOLD_OUT, backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        # 其他错误, 或没有加入购物车按钮
        if status_code != 200:

            log_info = json.dumps(
                dict(time=time.time(), title=pqhtml('title').text(), url=url))

            self.logger.info(log_info)

            data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get(
                'SCERR', 'ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        # 前期准备
        img_area = pqhtml('body div.left')
        prod_area = pqhtml('body .right')

        # print img_area.outerHtml().encode('utf-8')
        # print prod_area.outerHtml().encode('utf-8')
        # exit()

        # 下架
        if not prod_area :

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)
            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        detail = dict()

        # 产品ID
        productId = re.search(r'goods\/(\d+)[\/]?',url).groups()[0]
        detail['productId'] = productId
        detail['productSku'] = productId
        detail['productCode'] = productId

        # 品牌
        brand = prod_area('p:last').text().replace(u'进入品牌','').strip()
        detail['brand'] = brand

        # 名称
        detail['name'] = prod_area('#kuriosity_code').prev().text()

        # 货币
        currency = 'CNY'
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        # 价格
        price, listPrice = self.get_all_price(prod_area)
        detail['price'] = price
        detail['listPrice'] = listPrice

        # 退换货
        detail['returns'] = '' # img_area('div:last').text()

        # 描述
        img_area('div:last').empty()  # 清空售后说明
        detail['descr'] = prod_area('.text').text() + img_area('div:first').text()


        # 颜色
        # color = self.get_color(area)
        detail['color'] = self.cfg.DEFAULT_ONE_COLOR
        detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

        # 图片集
        imgs = [ 'https://www.k11kuriosity.com'+img.attr('src') for img in img_area('img.small').items()]
        detail['img'] = imgs[0]
        detail['imgs'] = imgs

        # 规格
        detail['sizes'] = self.get_sizes(prod_area)

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
        price = area('#price').text()

        if u'￥' not in price :
            raise Exception(u'price currency isn\'t CNY :{0}'.format(price))

        price = re.search(r'(\d[\d\.]*)', price).groups()[0]

        #自营渠道, 成本价*0.9
        # price = float(price)*0.9

        if not price :
            raise Exception('get price fail')

        return price,price

    def get_sizes(self,area):

        size_p = None

        for ele in area('p').items() :
            if u'尺码' in ele('span:first').text() :
                size_p = ele
                break
        else :
            raise Exception('get size block fail')

        sizes = []
        for button in size_p('button[pk!=""]').items():
            sizes.append(dict(
                name=button.text() or self.cfg.DEFAULT_ONE_SIZE,
                id=button.attr('kuriosity_code'),
                sku=button.attr('kuriosity_code'),
                inventory= button.attr('shop_num') or self.cfg.DEFAULT_STOCK_NUMBER,
                price=button.attr('price'),
                listPrice=button.attr('price')
            ))

        if not sizes :
            raise Exception('get sizes fail')

        return sizes
































