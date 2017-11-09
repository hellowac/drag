# coding=utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2017/01/20"

# 0.1 初始版
import re
import time
from pyquery import PyQuery
from collections import  defaultdict
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
        # area = pqhtml('.product-detail-information')
        # domain = tool.get_domain(url)
        skuMap,name2values = self.get_pdata(pqhtml)

        # print pqhtml.outerHtml().encode('utf-8')
        # exit()

        # 下架
        # if not area :
            # log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))
            # self.logger.info(log_info)
            # data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

            # return tool.return_data(successful=False, data=data)

        detail = dict()

        # 产品ID
        productId = pqhtml('input[id="item_id"]').attr('value')
        detail['productId'] = productId
        detail['productSku'] = productId
        detail['productCode'] = productId

        # 品牌
        brand = 'ZAOZUO'
        detail['brand'] = brand

        # 名称
        detail['name'] = pqhtml('input[id="item_name"]').attr('value')

        # 货币
        currency = 'CNY'
        detail['currency'] = currency
        detail['currencySymbol'] = tool.get_unit(currency)

        # 描述
        detail['descr'] = pqhtml('title').text() + pqhtml('.detail-wrapper').text()

        # 详细
        detail['detail'] = pqhtml('.detail-wrapper').text()

        # 退换货
        detail['returns'] = ''

        color_dict,imgs_dict,sizes_dict,prices_dict,listPrices_dict = self.get_all_info(skuMap, name2values)

        # print color_dict
        # print imgs_dict
        # print sizes_dict

        # 价格
        # price = pqhtml('input[id="itemMinPrice"]').attr('value')
        # listPrice = pqhtml('input[id="itemMaxPrice"]').attr('value')
        detail['price'] = prices_dict
        detail['listPrice'] = listPrices_dict

        # keys
        detail['keys'] = color_dict.keys()

        # 颜色
        detail['color'] = color_dict
        detail['colorId'] = {_id:_id for _id in color_dict.keys()}

        # 图片集
        common_imgs = [ ele_img.attr('src') for ele_img in pqhtml('#2 img').items()] or [ele_img.attr('src') for ele_img in pqhtml('.goods-detail-box img').items()]
        detail['img'] = { cid:_imgs[0] for cid,_imgs in imgs_dict.items()}
        map(lambda imgs : imgs.extend(common_imgs[:8]) , imgs_dict.values())
        detail['imgs'] = imgs_dict

        # 规格
        detail['sizes'] = sizes_dict

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

    def get_pdata(self,pqhtml):
        true = True
        false = False
        null = None

        for ele in pqhtml('script').items():
            if 'var skuMap' in ele.text():
                skuMap = re.search(r'var skuMap =(.*);\n\s', ele.text()).groups()[0]
                name2values = re.search(r'var name2values =(.*);\n\s', ele.text()).groups()[0]
                break
        else :
            raise Exception('get data fail')

        # print skuMap
        # print name2values

        skuMap = eval(skuMap)
        name2values = eval(name2values)

        return skuMap,name2values

    def get_all_info(self,skuMap,name2values):
        """ 获取颜色,尺码,图片信息。

        原网站比较麻烦，所以 代码比较长，并且定义了一个 函数以防止重复。
        color_id 和 size_sku 的构造不能改，依靠这两个ID来更新数据库。

        得鲜解析成指定的格式，在根据需求组合成我们需要的格式.

        1.先构造key
        2.然后根据key获取值.
        3.一个尺码一个商品

        """

        color_dict = {}
        size_dict = {}

        for nameId,values_list in name2values.items():
            for item in values_list:
                _name=item['value']

                _name = _name.decode('unicode-escape')

                _id = '{0}:{1}'.format(item['opNameId'],item['opValueId'])

                if item['imgSizeState'] == 1:
                    color_dict[_id]=_name

                # 0 和 2 均为款式比如 http://zaozuo.com/item/300089 和 http://zaozuo.com/item/300033
                elif item['imgSizeState'] in [0,2] :
                    size_dict[_id]=_name

        imgs_dict = defaultdict(list)
        sizes_dict = defaultdict(list)
        colors_dict = defaultdict(str)
        prices_dict = defaultdict(str)
        listPrices_dict = defaultdict(str)

        def to_add(_size_id,_size_name,_color_id,key):
            _product = skuMap.get(key,None)

            # 没有着这个产品[下架]
            if not _product:
                return

            _img = _product['longimg']      # +'@!small'
            _size = dict(
                name = _size_name,
                id=_size_id,
                sku=_size_id,
                inventory=_product['stock'] if _product['canBuy'] else 0,
                price = _product['price'],
                listPrice = _product['originalPrice']
            )

            imgs_dict[key].append(_img)
            sizes_dict[key].append(_size)
            colors_dict[key] = color_dict[_color_id]
            prices_dict[key] = _product['price']
            listPrices_dict[key] = _product['originalPrice']

        if size_dict and color_dict:
            for color_id, color_name in color_dict.items():
                for size_id, size_name in size_dict.items():
                    key = ';{0};{1};'.format(color_id,size_id)

                    to_add(size_id,size_name,color_id,key)
        elif not size_dict :
            for color_id,color_name in color_dict.items():
                key = ';{0};'.format(color_id)

                to_add(color_id,self.cfg.DEFAULT_ONE_SIZE,color_id,key)

        elif not color_dict :
            color_dict[self.cfg.DEFAULT_COLOR_SKU] = self.cfg.DEFAULT_ONE_COLOR
            for size_id, size_name in size_dict.items():
                key = ';{0};'.format(size_id)

                to_add(size_id,size_name,self.cfg.DEFAULT_COLOR_SKU,key)

        return colors_dict,imgs_dict,sizes_dict,prices_dict,listPrices_dict



















