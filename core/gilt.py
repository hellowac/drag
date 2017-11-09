#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/28"

#0.1 初始版
from . import DragBase
import re
import requests
from utils import tool


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)

    #获取页面大概信息
    def multi(self, url):
        pass


    #获取详细信息
    def detail(self, url):
        try:
            
            product_id = re.search(r'product/(\d+)-\w', url).groups()[0]

            api = 'https://api.gilt.com/v1/products/{product_id}/detail.json'
            params = dict(apikey=self.cfg.api_key)

            url = api.format(product_id=product_id)
            resp = requests.get(url, params=params)

            self.logger.debug('gilt product id:{0}, api response:{1}'.format(product_id, resp.text))

            if resp.status_code == 404:
                data = tool.get_off_shelf(code=resp.status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=resp.text)
                return tool.return_data(successful=False, data=data)

            elif resp.status_code != 200:
                data = tool.get_error(code=resp.status_code, message='gilt api status_code error:{0}'.format(resp.status_code), backUrl=resp.url, html=resp.text)
                return tool.return_data(successful=False, data=data)

            product_detail = resp.json()

            detail = dict()

            #产品ID
            productId = product_detail['id']
            detail['productId'] = productId

            #品牌
            brand = product_detail['brand']
            detail['brand'] = brand

            #名称
            detail['name'] = '{0} {1}'.format(brand, product_detail['name'])

            #货币
            currency = 'USD'  #  接口返回无货币单位，默认为美元。
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price, listPrice, color, sizes = self.get_info(product_detail)

            detail['price'] = price
            detail['listPrice'] = listPrice

            #颜色
            detail['color'] = color
            detail['colorId'] = productId

            #图片集
            img_urls = []
            for img_size,urls in product_detail['image_urls'].items():
                if img_size == '420x560':

                    img_urls = urls
                    break
            else:
                raise ValueError('get 420x560 imgs fail')

            imgs = [ img_url['url'] for img_url in img_urls]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = sizes

            #描述
            detail['descr'] = ' '.join(product_detail['content'].values()) or 'no descr'

            #退换货
            detail['returns'] = ''

            #HTTP状态码
            detail['status_code'] = 200

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = url
            
            #返回的IP和端口
            if resp.raw._original_response.peer :
                detail['ip_port']=':'.join(map( lambda x:str(x),resp.raw._original_response.peer))

            return tool.return_data(successful=True, data=detail)

        except Exception:
            raise

    def get_info(self, detail):

        color_names = []
        sizes = []
        prices = []
        list_prices = []

        for sku in detail['skus']:
            sku_id = sku['id']
            inventory = sku['units_for_sale']
            listPrice = float(sku['msrp_price'])
            price = float(sku['sale_price'])

            if 'attributes' in sku :
                color_name, size_name = self.get_color_and_size_name(sku['attributes'])
            else:
                color_name = self.cfg.DEFAULT_ONE_COLOR
                size_name =self.cfg.DEFAULT_ONE_SIZE

            obj = dict(id=sku_id, sku=sku_id, inventory=inventory, name=size_name, price=price, listPrice=listPrice)

            sizes.append(obj)
            prices.append(price)
            list_prices.append(listPrice)
            color_names.append(color_name)

        color_names = set(color_names)

        if len(color_names) != 1 :
            raise ValueError('color_name is more :{0}'.format(color_names))

        return max(prices), max(list_prices), color_names.pop(), sizes


    def get_color_and_size_name(self, attrs):
        colors = [ attr['value'].title() for attr in attrs if attr['name'] == 'color']
        color_name = '/'.join(colors)
        size_name = [ attr['value'].title() for attr in attrs if attr['name'] == 'size'][0]

        return color_name, size_name


