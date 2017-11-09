    #!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/29"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
# from requests_toolbelt import SSLAdapter
import re
import json
import time


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)
        # self.session.mount('https://', SSLAdapter('TLSv1'))
        # self.session.mount('https://', SSLAdapter('SSLv3'))
        # self.session.mount('https://', SSLAdapter('SSLv23'))


    #获取页面大概信息
    def multi(self, url):
        pass

    def detail(self,url):
        """ 2017-02-05 新增
        """
        
        #前期准备
        
        self.domain = tool.get_domain(url)
        url = url.split('?')[0] if '?' in url else url
        source = url[:url.rfind('/products')]
        source = source.split(self.domain)[1]

        resp = self.session.get(url, verify=False)

        permalink = url[url.rfind('/')+1:]

        #锁定当前链接关键字
        self.permalink = permalink

        status_code = resp.status_code

        #下架
        if status_code == 404 :
            pqhtml = PyQuery(resp.text)

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
            
            return tool.return_data(successful=False, data=data)

        #其他错误
        if status_code != 200 :
            pqhtml = PyQuery(resp.text)

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=json.dumps(log_info))

            return tool.return_data(successful=False, data=data)

        #2017-02-05 新增 该接口
        link = 'https://www.everlane.com/api/v2/product_groups?product_permalink={permalink}'.format(permalink=permalink)

        product_data = self.session.get(link, verify=False).json()

        details = self.get_products(product_data,permalink)

        for detail in details.values() :
            #HTTP状态码
            detail['status_code'] = status_code

            #返回链接
            detail['backUrl'] = url

            #本渠道特殊字段
            detail['everlaneApi'] = resp.url

        log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                              'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

        self.logger.info(log_info)

        return tool.return_data(successful=True, data=details)

    def get_products(self,product_data,permalink):
        """ 2017-02-05 新增
        """
        details = {}

        # print json.dumps(product_data)

        imgs_tmp = {'square': ['https://everlane-2.imgix.net/static/hero/20160110_DoubleKnit_Hero_Deliver.jpg']}

        for product in product_data['products']:
            key = product['permalink']
            detail = dict()

            # print json.dumps(product['variants'])
            detail['img'] = (product.get('albums', imgs_tmp).get('square') or ['not found'])[0]
            detail['name'] = product.get('display_name', 'Not Found')
            detail['imgs'] = map(lambda x: x+'&w=1200&h=1200',product.get('albums', imgs_tmp).get('square'))
            detail['price'] = product.get('price', 0)
            detail['color'] = product.get('color', {'name': self.cfg.DEFAULT_ONE_COLOR}).get('name')
            detail['brand'] = 'EVERLANE'
            detail['descr'] = product['details']['description'] if 'details' in product else None
            detail['video'] = product['video']['vimeo_url'] if 'video' in product and product['video'] else None
            detail['colorId'] = product['color']['hex_value']
            detail['currency'] = 'USD'                              #注意该货币符号固定的.
            detail['productId'] = product['id']
            detail['listPrice'] = product.get('traditional_price',None) or product['price']
            detail['currencySymbol'] = tool.get_unit('USD')
            detail['sizes'] = [ dict(
                                name=variant.get('abbreviated_size',variant.get('short_name',variant['name'])),
                                inventory=variant['inventory_count'] if variant['orderable_state'] == 'shippable' else 0,
                                sku=variant['id'],
                                id=variant['id']
                                ) 
                                for variant in product['variants'] ]
            detail['fabric'] = ' '.join(filter(lambda x : unicode(x),product['details']['fabric'].values())) if 'details' in product else None
            detail['model'] = ' '.join(map(lambda x : str(x), filter(lambda x : x,product['details']['model'].values()))) if 'details' in product else None
            detail['sizeFit'] = ' '.join(product['details']['fit']) if 'details' in product else None
            detail['madeIn'] = '; '.join(map(lambda x : ': '.join(x),product['details']['factory'].items())) if 'details' in product and 'factory' in product['details'] else None

            detail['status'] = self.cfg.STATUS_SALE

            details[key] = detail

        return details



    #获取详细信息
    def detail_old(self,url):
        #前期准备
        
        self.domain = tool.get_domain(url)
        url = url.split('?')[0] if '?' in url else url
        source = url[:url.rfind('/products')]
        source = source.split(self.domain)[1]

        resp = self.session.get(url, verify=False)

        link = '{domain}/api/v2{source}'.format(domain=self.domain, source=source)

        permalink = url[url.rfind('/')+1:]

        #锁定当前链接关键字
        self.permalink = permalink

        resp = self.session.get(link, verify=False)

        status_code = resp.status_code

        # print resp.url
        # print status_code
        # print resp.text.encode('utf-8')

        pdata = json.loads(resp.text)
        
        #下架
        if status_code == 404 :
            pqhtml = PyQuery(resp.text)

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
            
            return tool.return_data(successful=False, data=data)

        #其他错误
        if status_code != 200 :
            pqhtml = PyQuery(resp.text)

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=json.dumps(infos))

            return tool.return_data(successful=False, data=data)

        details = self.get_products(pdata,permalink)

        for detail in details.values() :
            #HTTP状态码
            detail['status_code'] = status_code

            #返回链接
            detail['backUrl'] = url

            #本渠道特殊字段
            detail['everlaneApi'] = resp.url

        log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                              'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

        self.logger.info(log_info)

        return tool.return_data(successful=True, data=details)

    def get_products_old(self,pdata,permalink):

        products = pdata['products']

        pgroup = pdata['groupings']['product_group']

        #查找当前链接的商品名称 做 key .
        display_name = None
        product_id = None

        for product in products :

            # print 'link:{2},\tdisplay_name:{0},id:{1}\n'.format(product['display_name'],product['id'],product['permalink'])

            if product['permalink'] == permalink :
                display_name = product['display_name']
                product_id = product['id']
                break

        if not display_name or not product_id :

            #http://www.everlane.com//collections//mens-newest-arrivals//products//mens-swim-short-navy
            #该链接会出现这种情况.
            
            source = permalink.split('-')[0] + '-all'

            link = 'https://www.everlane.com/api/v2/collections/{source}'.format(source=source)

            print link

            resp = self.session.get(link, verify=False)

            secondData = json.loads(resp.text) if resp.status_code == 200 else None

            if not secondData :
                raise ValueError('get product display_name and it\'s ID failure')

            return self.get_products(secondData,permalink)

        pIds = []

        for group in pgroup :
            if group['name'] == display_name and product_id in group['products']:       #有display name 重复的情况，所以要判断id是否在products组中.
                pIds = group['products']            #该结构为list
                break
        #---------------------------------------------------------

        #寻找并遍历找出符合ID的产品
        pArr = []

        for product in products :
            if product['id'] in pIds :

                pArr.append(product)
                continue
        #--------------------------------------------------------

        imgs_tmp = {'square': ['https://everlane-2.imgix.net/static/hero/20160110_DoubleKnit_Hero_Deliver.jpg']}

        #遍历产品.并返回.

        details = {}
        for product in pArr :
            key = product['permalink']
            detail = dict()
            detail['img'] = (product.get('albums', imgs_tmp).get('square') or ['not found'])[0]
            detail['name'] = product.get('display_name', 'Not Found')
            detail['imgs'] = map(lambda x: x+'&w=1200&h=1200',product.get('albums', imgs_tmp).get('square'))
            detail['price'] = product.get('price', 0)
            detail['color'] = product.get('color', {'name': self.cfg.DEFAULT_ONE_COLOR}).get('name')
            detail['brand'] = 'EVERLANE'
            detail['descr'] = product['details']['description'] if 'details' in product else None
            detail['video'] = product['video']['vimeo_url'] if 'video' in product and product['video'] else None
            detail['colorId'] = product['color']['hex_value']
            detail['currency'] = 'USD'                              #注意该货币符号固定的.
            detail['productId'] = product['id']
            detail['listPrice'] = product.get('traditional_price',None) or product['price']
            detail['currencySymbol'] = tool.get_unit('USD')
            detail['sizes'] = [ dict(
                                name=variant.get('short_name',variant['name']),
                                inventory=variant['inventory_count'] if variant['orderable_state'] == 'shippable' else 0,
                                sku=variant['id'],
                                id=variant['id']
                                ) 
                                for variant in product['variants'] ]
            detail['fabric'] = ' '.join(filter(lambda x : unicode(x),product['details']['fabric'].values())) if 'details' in product else None
            detail['model'] = ' '.join(map(lambda x : str(x), filter(lambda x : x,product['details']['model'].values()))) if 'details' in product else None
            detail['sizeFit'] = ' '.join(product['details']['fit']) if 'details' in product else None
            detail['madeIn'] = '; '.join(map(lambda x : ': '.join(x),product['details']['factory'].items())) if 'details' in product and 'factory' in product['details'] else None

            detail['status'] = self.cfg.STATUS_SALE

            details[key] = detail

        return details

    #处理数据
    def dispost(self,details):

        try:
            #获取当前链接颜色:
            if self.cfg.EVERLANE_ONE_COLOR :
            # if False:
                product = details[self.permalink]           #permalink 已在detail函数中添加
            else :
                product = details.values()


            attrs = self.cfg.ALL_DETAIL_ATTR
            must_attr = self.cfg.MUST_DETAIL_ATTR

            values = []


            #单颜色
            if isinstance(product,dict) :
                obj = dict()
                for attr in attrs :
                    try:

                        obj[attr] = product[attr] if isinstance(product[attr],dict) else product[attr]

                    except KeyError, e:
                        if e.message == attr and attr in must_attr :
                            raise Exception('{cname} must Key "{key}" is None'.format(cname=self.cfg.CFG_NAME.lower(),key=attr))

                        continue
                    
                values.append(obj)

                return values
            #多颜色
            elif isinstance(product,list) :

                for prod in product :

                    obj = dict()
                    for attr in attrs :
                        try:

                            obj[attr] = prod[attr] if isinstance(prod[attr],dict) else prod[attr]

                        except KeyError, e:
                            if e.message == attr and attr in must_attr :
                                raise Exception('{cname} must Key "{key}" is None'.format(cname=self.cfg.CFG_NAME.lower(),key=attr))

                            continue
                        
                    values.append(obj)

                return values

        except Exception, e:
            raise

    

