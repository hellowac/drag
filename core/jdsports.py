#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/06/22"

#0.1 初始优化版
from . import DragBase
from pyquery import PyQuery
from utils import tool
import re
import json
import time


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)


    #获取页面所有产品大概信息
    def multi(self, url):
       pass

        

    def detail(self,url):
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

            if status_code != 200 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message='status_code Error', backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            # area = pqhtml('#details')
            area = pqhtml('#productPage')

            # print area.outerHtml().encode('utf-8')
            # exit()


            detail = dict()

            currency = self.get_currency(pqhtml)

            price,listPrice = self.get_all_price(area)

            detail['status_code'] = status_code

            detail['price'] = price

            detail['listPrice'] = listPrice

            detail['currency'] = currency

            detail['currencySymbol'] = tool.get_unit(currency)

            detail['name'] = area('h1:first').text()

            detail['brand'] = area('a.itemBrand img').attr('alt') or area('h1:first').text().split()[0]

            detail['color'] = self.cfg.DEFAULT_ONE_COLOR

            detail['imgs'] = [img.attr('src') for img in area('ul.owl-carousel li>img:first').items()]

            detail['img'] = area('ul.owl-carousel li:first>img:first').attr('src')

            #官网最大数量为 9 
            sizes = [ dict(
                        name=button.text(),
                        sku=button.attr('data-sku'),
                        inventory=self.cfg.DEFAULT_STOCK_NUMBER if 'noStock' not in button.attr('class') else 0 ,
                        price=re.search(r'(\d[\.\d]*)',button.attr('data-price')).groups()[0],
                    ) for button in area('div#itemOptions .options>button').items()]

            detail['sizes'] = sizes

            #描述信息
            detail['descr'] = area('#itemInfoContainer .tabInf').text()

            #退货信息
            detail['returns'] = area('#itemInfoContainer .tabRet').text()

            #配送信息
            detail['delivery'] = area('#itemInfoContainer .tabDel').text()

            #产品ID
            product_id = area('input[name="productSku"]').attr('value')
            detail['productId'] = product_id
            detail['colorId'] = product_id

            #获取视频地址
            if len(area('.withVideo')) :
                detail['video'] = [ dict(link=source.attr('src'),type=source.attr('type')) for source in area('#videoWrp #productVideo source').items()]

            #获取特有的动图
            if area('input[name="productHasImageSpinSet"]').attr('value') == '1' :
                url = 'http://www.jdsports.co.uk/product/imageSpinSet/{pid}?height=656&width=656&debug=1'.format(pid=product_id)
                resp = self.session.get(url, verify=False)
                spinArr = [ i['resizingService']['resizedImage'] for i in json.loads(resp.text)]

                detail['spinImgSet'] = spinArr

            #商品状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回URL
            detail['backUrl'] = resp.url

            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)

            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise



    #获取所有价格
    def get_all_price(self,area):
        try:

            # print area.outerHtml().encode('utf-8')
            
            ptxt = area('div.itemPrices span[itemprop="price"]').attr('content').replace(',','')
            optxt = (area('div.itemPrices span.was').text() or ptxt ).replace(',','')

            price = re.search(r'(\d[\.\d]*)',ptxt).groups()[0]
            oldPrice = re.search(r'(\d[\.\d]*)',optxt).groups()[0]

            return price,oldPrice

        except Exception, e:
            e.message += 'function : get_all_price'
            raise


    #获取货币单位
    def get_currency(self,area):
        try:
            for ele in area('script').items() :
                if 'dataObject' in ele.text() :
                    currency = re.search(r'currency:"(.*?)"\s*',ele.text()).groups()[0]
                    return currency
        except Exception, e:
            e.message += 'function : get_currency'
            raise


    # # 处理数据
