#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/11/17"

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
        try:
            pass

        except Exception, e:
            raise


    #获取详细信息
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

            #其他错误
            if status_code != 200 :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_error(code=status_code, message=self.cfg.GET_ERR.get('SCERR','ERROR'), backUrl=resp.url, html=pqhtml.outerHtml())

                return tool.return_data(successful=False, data=data)
            
            #前期准备
            area = pqhtml('#goodsInfo')
            domain = tool.get_domain(url)
            # pdata = self.get_pdata(area)
            
            # print area.outerHtml().encode('utf-8')
            # exit()

            #下架
            if not area :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)
                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                
                return tool.return_data(successful=False, data=data)

            detail = dict()


            #产品ID
            productId = pqhtml('#goodsForm input#bskGodGodNo').attr('value')
            detail['productId'] = productId
            detail['productSku'] = productId
            detail['productCode'] = area('.prd-code').text()
            
            #品牌
            brand = pqhtml('#goodsForm input#brndNm').attr('value')
            detail['brand'] = brand

            #名称
            detail['name'] = u'{0} {1}'.format(brand,pqhtml('#goodsForm input#godNm').attr('value'))

            #货币,价格
            currency,price,listPrice = self.get_currency_prices(pqhtml,area)
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            detail['price'] = price
            detail['listPrice'] = listPrice

            #描述
            detail['descr'] = pqhtml('meta[name="description"]').attr('content')

            #详细
            detail['detail'] = pqhtml('meta[name="description"]').attr('content') + area('.desc-area').text()

            #颜色
            color = self.get_color(area)
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = self.cfg.DEFAULT_COLOR_SKU

            #图片集
            imgs = [ img.attr('src') for img in pqhtml('#prdImgWrap .prdImg ul>li>img').items()]
            detail['img'] = pqhtml('meta[property="og:image"][name="og_image"]').attr('content')
            detail['imgs'] = imgs

            #规格
            detail['sizes'] = self.get_sizes(area)

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


    def get_currency_prices(self,pqhtml,area):
        tmpTxt = area('.prd-price .prc:last').text().strip()

        # print tmpTxt

        currency,price = tmpTxt.split()[:2]

        meta_price = pqhtml('meta[property="product:sale_price:amount"]').attr('content')
        meta_listPrice = pqhtml('meta[property="product:price:amount"]').attr('content')

        if float(meta_price) != float(price) :
            raise ValueError('price:{0} not equal meta price:{1}'.format(price,meta_price))

        if len(currency) != 3 :
            raise ValueError('Currency:{0} lenth Error'.format(currency))

        return currency,price,meta_listPrice

    def get_color(self,area):
        nTxt = area('.prdTit').text().replace('\n','')

        if u'-' in nTxt :
            color = nTxt.split('-')[-1].strip()
        else :
            color = self.cfg.DEFAULT_ONE_COLOR

        if not color :
            raise ValueError('get color fail')

        return color

    def get_sizes(self,area):
        eles = area('.select-area .select-box-menu ul.sel-option input[name="sizeItmNo"][value!=""]')

        sizes = []
        for ele in eles.items():
            sID = ele.attr('value')
            sInv = ele.attr('onlineusefulinvqty')

            #不要/后面的汉字"售罄"
            sName = ele.prev()('em').text().split('/')[0]
            obj = dict(
                id=sID,
                sku=sID,
                name=sName,
                inventory=sInv,
            )

            sizes.append(obj)

        #另一种情况,http://cn.ssfshop.com/KNAVE/GP7816052195563/good?utag=ref_sch:KNAVE$set:$dpos:18
        if not sizes :
            for ele in area('.selWrap .sel_cnt ul>li>a').items():

                sName = ele.text()

                sizes.append(
                    dict(
                        id=ele.attr('optcd'),
                        sku=ele.attr('optcd'),
                        name=sName if ele.attr('statcd') == 'SALE_PROGRS' else sName.split('/')[0],
                        inventory=self.cfg.DEFAULT_STOCK_NUMBER if ele.attr('statcd') == 'SALE_PROGRS' else 0
                    )
                )

        if not sizes :
            raise ValueError('get sizes fail')

        return sizes








        



    

