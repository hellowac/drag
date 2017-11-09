#coding:utf-8

import re
import json
from pyquery import PyQuery

def amazon_unit(url):
    unit_dict = {
        'amazon.cn': ['￥', 'CNY'],
        'amazon.com': ['$', 'USD'],
        'amazon.co.jp': ['¥', 'JPY'],
        'amazon.com.br': ['R$', 'BRL'],        #巴西货币
        'amazon.ca': ['CDN$', 'CDN'],
        'amazon.fr': ['€', 'EUR'],
        'amazon.de': ['€', 'EUR'],
        'amazon.in': ['INR', 'INR'],
        'amazon.it': ['€', 'EUR'],
        'amazon.com.mx': ['$', 'MXN'],        #墨西哥币
        'amazon.es': ['€', 'EUR'],
        'amazon.co.uk': ['£', 'GRP']}        #英镑

    domain = re.search(r'http[s]?://([\w\.]*)/',url).groups()[0].replace('www.','')

    for k, v in unit_dict.items():
        if k == domain:
            unit = v[0]
            currency = v[1]

            return unit,currency
    else :
        raise ValueError,'get Amazon Unit Fail'



def amazon_convert_imgKey(inst,sizes,imgsData):

    # print json.dumps(sizes) 
    # print json.dumps(imgsData)

    #处理官网imgs的key 为 'One Size' 的情况.
    if isinstance(imgsData,dict) and len(imgsData.keys()) == 1 and imgsData.keys()[0].lower() == 'one size' :
        imgsData = {inst.cfg.DEFAULT_ONE_COLOR:imgsData.values()[0]}

    #处理官网One color 情况.
    if isinstance(sizes,dict) and len(sizes) == 1 and sizes.keys()[0] == inst.cfg.DEFAULT_ONE_COLOR and isinstance(imgsData, dict) :
        imgsData = {inst.cfg.DEFAULT_ONE_COLOR:imgsData.values()[0]}
        
    convert=[]
    if isinstance(sizes,dict) :
        for s,item in sizes.items() :
            arr = s.split()
            arr.sort()
            convert.append((' '.join(arr),s))

    imgs = {}
    tmp= {}
    if isinstance(imgsData,dict) :
        for k,item in imgsData.items() :
            arr = k.split()
            arr.sort()
            d = ' '.join(arr)
            for c in convert :
                if d == c[0] :
                    imgs[c[1]]=item
                    break
                elif c[0] in d and c[1] not in tmp :
                    tmp[c[0]]={len(item):item}
                    break
                elif c[0] in d and c[1] in tmp :
                    tmp[c[0]][len(item)]=item
                    break
            else :
                if isinstance(sizes,dict) and len(sizes.keys()) != len(imgsData.keys())  and k in str(sizes) :
                    imgs = [ img for imgs_ in imgsData.values() for img in imgs_]
                else :
                    # print '++++++++++warning : Convert imgs Key {k} Fail'.format(k=k)
                    raise ValueError,'Convert imgs Key {k} Fail'.format(k=k)

    elif isinstance(imgsData,list) :
        imgs = imgsData

    #获取颜色中图片最多的集合
    if tmp :
        for k,item in tmp.items():
            arr=item.keys()
            arr.sort()
            key=arr[-1]
            imgs[k]=tmp[k][key]

    return imgs


def amazon_size_link_asinDetail(response):

    from .amazon_general import amazon_general_name, amazon_general_price, amazon_general_oldPrice

    content=re.sub(r'\s*&&&\s*',',',response.content)

    null=None
    exec 'Arr=[{c}]'.format(c=content)

    #解析数据
    inv=0
    name=''
    brand=''
    descr=''
    price=0
    oldPrice=0
    for item in Arr :
        f=item['FeatureName']

        if inv and name and brand and descr and price and oldPrice :
            return dict(name=name,brand=brand,descr=descr,price=price,oldPrice=oldPrice,inv=inv)

        #品牌
        # if f=='brandByline_feature_div' :
        if f[:4]=='brand' :
            c=item['Value']['content'][f]
            if not c or not c.strip() :
                continue

            brand=c

        elif f[:5]=='price' :
            c=item['Value']['content'][f]
            if not c or not c.strip() :
                continue
            price= amazon_general_price(PyQuery(c).remove('script').remove('style'))
            oldPrice= amazon_general_oldPrice(PyQuery(c).remove('script').remove('style'))

        elif f[:5]=='title' :
            c=item['Value']['content'][f]
            if not c or not c.strip() :
                continue
            name= amazon_general_name(PyQuery(c.replace('\/','/')).remove('script').remove('style'))

        elif f in ['featurebullets_feature_div','product-description_feature_div','productDescription_feature_div'] :
            c=item['Value']['content'][f]
            if not c or not c.strip() :
                continue
            # print f
            # print c
            descr+=PyQuery(c.replace('\/','/')).remove('script').remove('style').text()

        elif f[:6]=='buybox' :
            c=item['Value']['content'][f]
            if not c or not c.strip() :
                continue
            pqhtml=PyQuery(c.replace('\/','/'))

            inv=pqhtml('select#quantity option:last').attr('value') or 0

            if not inv and 'Only' in pqhtml('#soldByThirdParty .a-color-success').text() :
                inv = int(re.search(r'Only\s*(\d*)\s*',pqhtml('#soldByThirdParty .a-color-success').text()).groups()[0])

    #Feature:
        # title_feature_div : 名称模块
        # price_feature_div : 价格模块
        # brandByline_feature_div : 品牌模块
        # averageCustomerReviews_feature_div : 商品评论星星数
        # productGuarantee_feature_div : 商品担保模块
        # tellAFriendJumpbar_feature_div : 好友分享
        # price_feature_div : 价格模块
        # applicablePromotionList_feature_div : 促销模块
        # returnable_feature_div : 退换承诺
        # featurebullets_feature_div : 说明模块
        # buybox_feature_div : 一键下单模块
        # moreBuyingChoices_feature_div 更多购买选择
        # giftCardDiscovery_feature_div 购物卡余额模块
        # promotionUpsell_feature_div 商品促销和特殊优惠
        # productDescription_feature_div 商品描述模块
        # dpx-promotion-upsell_feature_div 商品促销和特殊优惠
        # buyxgety_feature_div 经常一起购买的商品
        # purchase-similarities_feature_div 相似商品
        # upsellrecommendation_feature_div 追加购买产品建议
        # detail-bullets_feature_div 商品基本信息
        # conditional-probability_feature_div 其他顾客购买后购买的商品
        # product-predicted-rating-detail_feature_div 评论规则
        # ask-btf_feature_div 买家问题
        # customer-reviews_feature_div 客户评论模块
        # browse_feature_div 查找其它相似商品
        # hero-quick-promo-grid_feature_div 更多商品促销信息
        # availability_feature_div 在库状况
        # amazonGlobalStore-tips_feature_div amazon全球购说明

    return dict(productName=name,brand=brand,descr=descr,price=price,listPrice=oldPrice,inventory=inv)
