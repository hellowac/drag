#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/08/12"

#0.1 初始版
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


    #获取页面大概信息
    def multi(self, url):
        pass


    def detail(self,url):
        try:
            
            self.domain = tool.get_domain(url)

            if 'web1.sasa.com' in self.domain :
                return self.detail_by_hk(url)

            elif 'www.sasa.com' in self.domain :
                return self.detail_by_www(url)

        except Exception, e:
            raise


    #获取香港产品详细信息
    def detail_by_hk(self,url):
        try:
            resp = self.session.get(url, verify=False)

            status_code = resp.status_code
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
            area = pqhtml('#Main')
            # pdata = self.get_pdata(pqhtml)
            # roter,goodsData = self.get_goodsData(pqhtml)
            
            # print area.outerHtml().encode('utf-8')
            # print self.session.cookies.get_dict()
            # {'currency': '2', 'location': '3', 'T7_JSESSIONID': '308B6C0438C94F52A4048588D1E9D551', 'previous1': '10093665'}
            # print area.outerHtml()
            # exit()

            #下架
            if u'缺货' in area('.detail-size form font').text() :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = area('.detail-info .right span[itemprop="brand"]').text()
            detail['brand'] = brand

            #名称
            detail['name'] = brand + ' '+area('.detail-info .right span[itemprop="name"]').text()

            #货币,和cookie设置的值一致.web1域名为HK
            currency = 'HKD'    
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_price_by_hk(area)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #产品ID
            productId = self.get_prdId_by_hk(area)
            detail['productId'] = productId

            #颜色
            # color = self.get_color(area)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = productId

            #图片集
            imgs = [ a.attr('src') for a in pqhtml('#big_pic img').items()]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=productId,id=productId)]

            #描述
            detail['descr'] = area('.detail-item').text()

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url
            
            #返回的IP和端口
            if resp.raw._original_response.peer :
                detail['ip_port']=':'.join(map( lambda x:str(x),resp.raw._original_response.peer))

            log_info = json.dumps(dict(time=time.time(), 
                                       productId=detail['productId'], 
                                       name=detail['name'], 
                                       currency=detail['currency'], 
                                       price=detail['price'], 
                                       listPrice=detail['listPrice'], 
                                       url=url))

            self.logger.info(log_info)


            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise



    def get_prdId_by_hk(self,area):

        for div in area('.detail-info .right .content div').items() :
            if u'產品號碼' in div.text() :
                prd_Id = re.search(r'(\w*)\b',div.text()).groups()[0]
                break
        else :
            info_txt = area('.detail-info .right span[itemprop="name"]').parent().attr('href')
            prd_Id = re.search(r'itemno=(\w*)\b',info_txt).groups()[0]

        if not prd_Id :
            raise ValueError('Get product_id Fail')

        return prd_Id


    #获取港币价格
    def get_price_by_hk(self,area):
        ptxt = area('.detail-info .right .content big').text()

        if 'HK$' not in ptxt :
            raise ValueError('get HKD price Fail')

        price = re.search(r'(\d[\.\d]*)',ptxt).groups()[0]

        for div in area('.detail-info .right content div').items() :
            if u'建議價' in div.text() or u'建议价' in div.text() :
                listPrice = re.search(r'(\d[\.\d]*)',div.text()).groups()[0]
                break 
        else :
            listPrice = price

        if not price or not listPrice :
            raise ValueError('Get price Fail')

        return price,listPrice


    #获取内地详细信息
    def detail_by_www(self,url):
        try:
            resp = self.session.get(url, verify=False)

            status_code = resp.status_code
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
            area = pqhtml('#main #product_container')
            pdata = self.get_pdata(pqhtml)
            roter,goodsData = self.get_goodsData(pqhtml)
            
            # print pqhtml.outerHtml()
            # print area.outerHtml()
            # exit()

            #下架
            if roter['soldOut'] :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            detail['brand'] = pdata['sc_brandENG']

            #名称
            detail['name'] = area('.product-titles').text()

            #货币,和pdata中['sc_priceRMB'] 绑定
            currency = 'CNY'    
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(roter)
            detail['price'] = price
            detail['listPrice'] = listPrice or price

            #产品ID
            productId = pdata['sc_prdSKU'] or roter['goods_id']
            detail['productId'] = productId

            #颜色
            # color = self.get_color(area)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = productId

            #图片集
            imgs = [ a.attr('href') for a in pqhtml('.product-album-thumb .thumbnail a').items()]
            detail['img'] = imgs[0]
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = self.get_sizes(roter)

            #描述
            detail['descr'] = pqhtml('.product-attributes').text() + pqhtml('.product_detail').text()

            #详细
            detail['detail'] = pqhtml('.product_detail').text()

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = resp.url
            
            #返回的IP和端口
            if resp.raw._original_response.peer :
                detail['ip_port']=':'.join(map( lambda x:str(x),resp.raw._original_response.peer))

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


    def get_sizes(self,roter):
        interface = roter['stock_link']

        data = self.session.get(interface, verify=False).text

        inv = json.loads(data)['store']

        return [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=inv,sku=roter['goods_id'],id=roter['goods_id'])]


    def get_all_price(self,roter):
        interface = roter['price_link']
        data = self.session.get(interface, verify=False).text
        data = json.loads(data)

        print json.dumps(data)

        return data['price'],data['mktprice']


    def get_goodsData(self,pqhtml):
        for script in pqhtml('script').items():

            if '_goodsData' in script.text() :
                goodsData = re.search(r'var _goodsData = (\{.*\});\s*var storage',script.text(),re.DOTALL).groups()[0]
                break

        for script in pqhtml('script').items():
            if 'var Router' in script.text():

                roter = re.search(r'var Router = \{(.*\s*)\};\s*var\s*Query',script.text(),re.DOTALL).groups()[0]
                break

        if not goodsData or not roter:

            raise ValueError('Get pdata Fail')


        soldOut = re.search(r'soldOut:(\d),',goodsData).groups()[0]

        goods_id = re.search(r'id:\'(.*)\',',goodsData).groups()[0]

        price_interface = re.search(r'price: function\(id\)\s*\{\s*return (.*);\s*\},\s*stock',roter,re.DOTALL).groups()[0]

        stock_interface = re.search(r'stock: function\(id\)\s*\{\s*return (.*);\s*\},\s*basic',roter,re.DOTALL).groups()[0]


        #限时特卖
        if 'seckill-ajax' in price_interface :
            goods_id = pqhtml('form#seckilladdcartform input[name="goods[seckill_id]"]').attr('value')
        elif 'goods-ajax' in price_interface :
            goods_id = pqhtml('form#seckilladdcartform input[name="goods[goods_id]"]').attr('value')

        # print roter.encode('utf-8')
        # print price_interface.replace('id',"'{0}'".format(goods_id)).encode('utf-8')
        # print stock_interface.replace('id',"'{0}'".format(goods_id)).encode('utf-8')

        price_url = self.domain + eval(price_interface.replace('id',"'{0}'".format(goods_id)))
        stock_url = self.domain + eval(stock_interface.replace('id',"'{0}'".format(goods_id)))

        Roter = dict(price_link=price_url,
                     stock_link=stock_url,
                     goods_id=goods_id,
                     soldOut=int(soldOut))

        return Roter,goodsData


    def get_pdata(self,pqhtml):
        for script in pqhtml('script').items():

            if 'page_data' in script.text() :
                page_data = json.loads(re.search(r'page_data = JSON\.parse\(\'(.*)\'\);',script.text()).groups()[0])
                break
        else :
            raise ValueError('Get pdata Fail')

        return page_data

