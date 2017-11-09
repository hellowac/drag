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
import re
import json
import time
import traceback


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)


    #获取页面大概信息
    def multi(self, url):
        pass

    #获取详细信息
    def detail(self,url):
        resp = self.session.get(url, verify=False)

        status_code = resp.status_code
        pqhtml = PyQuery(resp.text) if resp.text else False

        #下架
        if status_code == 404 or pqhtml is False:

            title = pqhtml('title').text() if pqhtml is not False else 'nothing'
            log_info = json.dumps(dict(time=time.time(),title=title,url=url))

            self.logger.info(log_info)

            html = pqhtml.outerHtml() if pqhtml is not False else 'nothing'
            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=html)
            return tool.return_data(successful=False, data=data)

        if status_code != 200 :

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)

        #前期准备
        area = pqhtml('.pdp_wrap>div.eagle') or pqhtml('#main-content .g')      #后面的这个是新加的(2016-11-17)

        sizes = self.get_sizes(area)

        # print area.html().encode('utf-8')
        # print pqhtml.outerHtml()
        # exit()

        #下架
        if not sizes or pqhtml('input#sizeValue').attr('value') == 'Sold Out':

            log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

            self.logger.info(log_info)

            data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())

            return tool.return_data(successful=False, data=data)
        
        detail = dict()

        #名称
        detail['name'] = area('h1[property="name"]').text()

        #产品ID
        # productId = re.search(r'productId: "(.*?)",',area('script').text(),re.DOTALL).groups()[0]
        productId = pqhtml('input#productCode').attr('value')
        detail['productId'] = productId
        detail['colorId'] = productId

        #描述
        detail['descr'] = area('ul.product-details__list').text()

        #品牌
        detail['brand'] = area('[property="brand"]').text() or pqhtml('[property="brand"]').text() or area('.u-margin-a--none:first').text()

        #货币符号
        try:
            currency = pqhtml('meta[property="wanelo:product:price:currency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)
        except KeyError as e:
            print resp.status_code
            print pqhtml.outerHtml().encode('utf-8')
            # print traceback.print_exc()
            exit()
        

        #价格
        price,listPrice = self.get_all_price(area)
        price = pqhtml('meta[property="wanelo:product:price"]').attr('content').replace(',','')
        detail['price'] = price
        detail['listPrice'] = listPrice


        #颜色
        detail['color'] = area('.pdp_color #colorText').text() or area('.selectedColor').text() or self.cfg.DEFAULT_ONE_COLOR

        #图片集
        imgsTmp = [ele.attr('data-image') for ele in area('div.slideshow__pager>a').items()]
        detail['img'] = imgsTmp[0]
        detail['imgs'] = imgsTmp

        #规格
        detail['sizes'] = sizes

        #设计者
        detail['designer'] = area('p.product-details__copy').text()

        #HTTP状态码
        detail['status_code'] = status_code

        #状态
        detail['status'] = self.cfg.STATUS_SALE

        #返回链接
        detail['backUrl'] = resp.url
        
        #返回的IP和端口
        if resp.raw._original_response.peer :
            detail['ip_port']=':'.join(map( lambda x:str(x),resp.raw._original_response.peer))

        log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                              'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

        self.logger.info(log_info)

        return tool.return_data(successful=True, data=detail)
    
    #获取数据
    def get_pdata(self,Jtxt):
        
        g = re.search(r'productDetails: (.*?)skuJournal',Jtxt,re.DOTALL).groups()[0]

        if g is not None :
            return json.loads(g.strip()[:-1])
        else :
            raise ValueError,'productDetails is None'

    
    def get_all_price(self,area):
        ptxt = area('.prices>.prices__retail').text() or area('.prices>.prices__markdown').text()

        # print area.html().encode('utf-8')
        # print ptxt
        # exit()

        # ptxt = ptxt.replace(',','')

        price = re.search(r'(\d[\.\,\d]*)',ptxt,re.DOTALL).groups()[0]

        ptxt = area('.prices *[class^="prices__retail"]').text()

        #当为欧元时，替换逗号为点.
        if u'€' in ptxt :
            ptxt = ptxt.replace(',','.')

        listPrice = re.search(r'(\d[\,\.\d]*)',ptxt,re.DOTALL).groups()[0]

        listPrice = listPrice.replace(',','')

        return price,listPrice


    def get_sizes(self,area):
        
        try:
            sizeElements = area('ul#size-ul>li>a')

            if not sizeElements : sizeElements = area('ul#size-ul>li>button')

            sizes = []

            for ele in sizeElements.items() :

                # if ele.hasClass('size-clickable') :
                #     inv = ele.attr('data-qty')
                # else :
                #     inv = 0

                obj = dict(
                    name=ele.text().replace('US','').strip(),
                    id=ele.attr('data-size'),
                    sku=ele.attr('data-size'),
                    inventory = int(ele.attr('data-qty')),
                    # eleHtml=ele.outerHtml(),
                    # hasable=ele.hasClass('size-clickable'),
                    # dataqty=ele.attr('data-qty'),
                )

                sizes.append(obj)

            # sizes = [
            #     {
            #         'name':ele.text().replace('US','').strip(),
            #         'sku':ele.attr('data-size'),
            #         'inventory':ele.attr('data-qty') if ele.hasClass('size-clickable') else 0 ,
            #         # 'inventory':ele.attr('data-qty') if ele.attr('data-qty') != 'null' and ele.hasClass('size-clickable') else 0 ,
            #         'eleHtml':ele.outerHtml()
            #     } 
            #     for ele in sizeElements.items()
            # ]

            # sizes = [{'name':ele.text(),'sku':ele.attr('data-size'),'inventory':ele.attr('data-qty') if ele.attr('data-qty') != 'null' and ele.hasClass('size-clickable') else 0 } for ele in sizeElements.items()]

            #one size
            if not sizes and not area('#addtobagbutton').attr('style'):
                inv = self.cfg.DEFAULT_STOCK_NUMBER

                flag = area('.product-badges').text()
                flag1 = area('input.cantfindsize').attr('value') or ''

                if u'售罄' in flag or 'Out Of Stock' in flag :
                    inv = 0
                elif u'通知我' in flag1 or 'Notify Me'in flag1 :
                    inv = 0

                
                sizes = [{'name':self.cfg.DEFAULT_ONE_SIZE,'inventory':inv,'sku':'001'}]

            return sizes

        except Exception, e:
            raise




