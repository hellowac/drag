#!/usr/bin/python
# coding=utf-8

import json
import time
import traceback
from datetime import datetime
from requests.exceptions import ReadTimeout, ConnectTimeout

from cfg import InstanceCfg
from core import Draws
from utils import tool


# detail
# --------------,
durls = [
    'http://item.yintai.com/21-185-1164C.html',
    'http://www.footpatrol.co.uk/footwear/248627-x-horween-classic-leather.html',
    'http://www.footpatrol.co.uk/footwear/026520-air-force-1-mid-lv8.html',     # 404
    # 'http://www.wconcept.cn/catalog/product/view/id/35108',
    # 'http://zaozuo.com/item/300089',
    # 'http://zaozuo.com/item/300175',
    # 'http://zaozuo.com/item/300101',
    'http://zaozuo.com/item/300132',
    # 'https://developer.mozilla.org/zh-CN/docs/Web/Guide/CSS',
    # 'http://www.sheisback.com/cn/?menuType=product&mode=view&act=list&page=12&searchField=&searchKey=&lcate=034&mcate=&scate=&fcate=&sort=&prodCode=2017022200004&searchIcon6=&searchIcon7=&searchIcon8=&searchIcon9=&searchColor=&searchSize=&pr_no=247&searchStartPrice=&searchEndPrice=',
    # 'https://www.everlane.com/products/mens-slim-pant-grey?collection=mens-pants',
	# 'https://factory.jcrew.com/mens_clothing/new_arrivals/sweaters/PRDOVR~E3748/E3748.jsp?color_name=hthr-sesame',
	# 'https://factory.jcrew.com/mens_clothing/new_arrivals/sweaters/PRDOVR~E3748/E3748.jsp?color_name=hthr-sesame',
]

class Drag(object):

    def __init__(self):
        self.logger = InstanceCfg.LOGGER

    # 扫描redis获取产品详细结果
    def url_detail(self, url=None):
        try:
            detail = [dict(link=url, status=InstanceCfg.STATUS_ERROR,
                           message='init detail list to return , return data shouldn\'t is this , check this link')]
            if url:

                channel_name = tool.get_domain_name(url)

                # 获取渠道实例
                instance = Draws(channel_name)

                result = instance.detail(url)

                if not result:
                    raise ValueError('get detail fail, instance\'s detail return None')

                if result['successful']:
                    # 根据配置文件返回抓取到的数据
                    detail = instance.dispost(result['data'])
                    map(lambda d: d.update(link=url), detail)

                    # 检验数据必须字段是否有值
                    tool.check_drag_detail(detail)

                if not result['successful']:
                    # 判断是抓取失败还是sold out
                    detail = result['data']
                    detail['link'] = url
                    detail = [detail]
            else:
                raise ValueError('Check Drag url :{}'.format(url))

        except ConnectTimeout:
            detail = [dict(link=url, status=InstanceCfg.STATUS_ERROR,
                           message='request connect time out')]

        except ReadTimeout:
            detail = [dict(link=url, status=InstanceCfg.STATUS_ERROR,
                           message='request read time out')]

        except Exception:
            self.logger.exception('"url_details:%s"' % url)
            detail = [dict(link=url, status=InstanceCfg.STATUS_ERROR,
                           message=traceback.format_exc().split('\n'))]
            raise

        finally:

            # 增加抓取时间
            map(lambda d: d.update(t=datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S')), detail)
            map(lambda d: d.update(t_stamp=str(int(time.time() * 100))), detail)

        return detail

    # 扫描redis获取产品大概结果
    def url_multi(self, url=None):
        if url:

            instance = self.get_instance(url)

            result = instance.multi(url)

            if result['successful']:
                # 根据配置文件返回抓取到的数据
                multi = result['data']

            if not result['successful']:
                # 判断是抓取失败还是sold out
                multi = result['data']

            return multi

        else:
            raise ValueError('Check factory url_multi url :{}'.format(url))

    def amazon_size_link_detail(self, link):
        try:
            detail = [dict(link=link, status=InstanceCfg.STATUS_ERROR,
                           message='init detail list to return , return data shouldn\'t is this , check this link')]
            if link:

                channel_name = 'amazon'

                # 获取渠道实例
                instance = Draws(channel_name)

                result = instance.size_link_detail(link)

                if not result:
                    raise ValueError('get detail fail, instance\'s detail return None')

                detail = result['data']
                detail['link'] = link

                # 判断数据是否正确看状态status_code 字段.
            else:
                raise ValueError('use brower verify amazon '
                                 'size detail link :{0}'.format(link))
        except Exception :
            self.logger.exception('"amazon_size_link_detail:%s"' % link)
            detail = dict(link=link, status=InstanceCfg.STATUS_ERROR,
                          message=traceback.format_exc().split('\n'))

        finally:
            # 增加抓取时间
            detail['t'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            detail['t_stamp'] = str(int(time.time() * 100))

            return detail


if __name__ == '__main__':
    drag = Drag()

    # url ='https://www.amazon.co.jp/gp/twister/ajaxv2?sid=353-2057628-5653451&ptd=HEALTH_PERSONAL_CARE&smid=AN1VRQENFRJN5&sCac=1&twisterView=glance&pgid=health_and_beauty_display_on_website&rid=5B59KTZCWQZ7M1C9T9A0&dStr=size_name&auiAjax=1&json=1&dpxAjaxFlag=1&isUDPFlag=1&ee=2&nodeID=160384011&parentAsin=B00MB130U8&enPre=1&dcm=1&udpWeblabState=T1&storeID=hpc&psc=1&asinList=B00NNJ4O5W&isFlushing=2&dpEnvironment=hardlines&id=B00NNJ4O5W&mType=full'
    # url ='https://www.amazon.co.jp/gp/twister/ajaxv2?sid=352-3683674-7562064&ptd=HEALTH_PERSONAL_CARE&smid=AN1VRQENFRJN5&sCac=1&twisterView=glance&pgid=health_and_beauty_display_on_website&rid=3XRSMTYVYX14W5MEH1G2&dStr=size_name&auiAjax=1&json=1&dpxAjaxFlag=1&isUDPFlag=1&ee=2&nodeID=160384011&parentAsin=B00MB130U8&enPre=1&dcm=1&udpWeblabState=T1&storeID=hpc&psc=1&asinList=B0019C9KMC&isFlushing=2&dpEnvironment=hardlines&id=B0019C9KMC&mType=full'
    # result = drag.amazon_size_link_detail(url)
    # print json.dumps(result)
    # exit()

    # detial测试

    res = drag.url_detail(durls[-1])
    # for r in res:
    #     if 'amazon_need_wait' in r and r['amazon_need_wait'] :
    #         for s in r['sizes'] :
    #             link = s['link']
    #             sz_info = drag.amazon_size_link_detail(link)
    #             # print json.dumps(sz_info)
    #             s['price'] = sz_info['price']
    #             s['listPrice'] = sz_info['listPrice']
    #             s['inventory'] =sz_info['inventory']

    print(json.dumps(res).encode('utf-8'))

    # amzon 校验

    # link = res[0]['sizes'][0]['link']

    # size_detail = drag.amazon_size_link_detail(link)

    # print json.dumps(link)
    # print json.dumps(size_detail)
