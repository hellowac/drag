# coding=utf-8
 
import re
import time

from pyquery import PyQuery
from .amazon_util import amazon_unit,amazon_convert_imgKey


def wait_distill(inst,leftCol,rightCol,centerCol,pqhtml):
    unit,currency = amazon_unit(inst.url)
    imgsData = amazon_general_imgs(leftCol,pqhtml)

    #不发ajax获取详细信息.
    sizes = amazon_general_info_wait(inst,pqhtml)

    if not sizes : 
        sizes = amazon_general_oneSize(inst,centerCol,rightCol)
        #需要延时获取？
        inst.need_wait = False

    else :
        inst.need_wait = True
        
    name=amazon_general_name(centerCol)
    brand=amazon_general_brand(centerCol)
    descr=amazon_general_descr(centerCol,pqhtml)
    price=amazon_general_price(centerCol)
    listPrice=amazon_general_oldPrice(centerCol)

    skus = sizes.keys() if isinstance(sizes,dict) else None
    color = dict([(k,k) for k in sizes]) if isinstance(sizes,dict) else inst.cfg.DEFAULT_ONE_COLOR
    imgs = amazon_convert_imgKey(inst,sizes,imgsData)

    productId = pqhtml('form#addToCart input[name="ASIN"]').attr('value')

    detail = dict()

    detail['brand'] = brand
    detail['name'] = name
    detail['currency'] = currency
    detail['currencySymbol'] = unit
    detail['price'] = price
    detail['listPrice'] = listPrice
    detail['color'] = color
    detail['colorId'] = {key:key for key in color.keys() } if isinstance(color,dict) else productId
    detail['img'] = {key:imgArr[0] for key,imgArr in imgs.items() } if isinstance(imgs,dict) else imgs[0]
    detail['imgs'] = imgs
    detail['productId'] = productId
    detail['sizes'] = sizes
    detail['descr'] = descr

    #多颜色
    if isinstance(sizes,dict) :
        detail['keys'] = sizes.keys()


    return detail


def amazon_general_info_wait(inst,pqhtml):

    # print pqhtml.outerHtml().encode('utf-8')

    # exit()
    #获取一个参数:
    environmentTxt = None
    for i,ele in enumerate(pqhtml('#twisterJsInitializer_feature_div script').items()):
        # print i
        # print ele.text()
        if 'dpEnvironment' in ele.text() :
            environmentTxt = ele.text()
    # print environmentTxt
    #获取参数数据DATA
    if environmentTxt :
        r = re.search(r'\s*var\s*(dataToReturn =.*);\s*return dataToReturn;',environmentTxt,re.DOTALL)
        if r :
            null=None
            true=True
            false=False
            exec r.groups()[0]
            dpxData=dataToReturn
            # print json.dumps(dpxData)
            dpEnvironment=dpxData['dpEnvironment']
        else :
            raise ValueError,'get dpEnvironment Fail'
    else :
        dpEnvironment='hardlines'
        # print '+++++++Warning: Get dpEnvironment Fail'
        return None

    #判断页面数据位置
    for i,ele in enumerate(pqhtml('script').items()):
        # print i
        # print ele.outerHtml()
        if 'useTwisterJsInitFromDPXPartially' in ele.text() :
            dataToReturnTxt = ele.text()
            break
    else :
        raise ValueError,'search dataToReturn Fail'

    dataToReturnTxt = dataToReturnTxt.replace('//selectively not escaping this.','')
    #获取页面数据JSON
    r = re.search(r'\s*var\s*(dataToReturn =.*?);\s*return dataToReturn;',dataToReturnTxt,re.DOTALL)
    if r :
        null=None
        true=True
        false=False
        exec r.groups()[0]

        data = amazon_general_size_wait(inst,dataToReturn,dpEnvironment,
            asinVariationValues=dpxData['asinVariationValues'] or None,
            displayLabels=dpxData['variationDisplayLabels'] or None,
            variationValues=dpxData['variationValues'] or None)

        return data
    else :
        raise ValueError,'get dataToReturn Fail'

    raise ValueError,'Get Sizes Fail'


def amazon_general_size_wait(inst,dataToReturn,dpEnvironment,
    asinVariationValues=None,displayLabels=None,variationValues=None):

    # print json.dumps(dataToReturn)
    # 判断页面都有哪些尺码
    displayLabels = dataToReturn['variationDisplayLabels'] or displayLabels
    hasSize='size_name' in displayLabels
    hasColor='color_name' in displayLabels
    hasStyle='style_name' in displayLabels
    hasEdition='edition' in displayLabels
    hasPackage='customer_package_type' in displayLabels

    # 尺码对应的值数组
    variation_values=dataToReturn['variation_values'] or variationValues
    size_name=variation_values['size_name'] if hasSize else None
    color_name=variation_values['color_name'] if hasColor else None
    style_name=variation_values['style_name'] if hasStyle else None
    edition_name=variation_values['edition'] if hasEdition else None
    package_name=variation_values['customer_package_type'] if hasPackage else None

    blink=inst.domain+dataToReturn['twisterUpdateURLInfo']['immutableURLPrefix']

    #构造数据
    color_asins={}
    asin_to_values = dataToReturn['asin_variation_values'] or asinVariationValues
    for asin,item in asin_to_values.items() :
        sizeName = size_name[int(item['size_name'])] if hasSize else ''
        colorName = color_name[int(item['color_name'])] if hasColor else ''
        styleName = style_name[int(item['style_name'])] if hasStyle else ''
        editionName = edition_name[int(item['edition'])] if hasEdition else ''
        packageName = package_name[int(item['customer_package_type'])] if hasPackage else ''

        #构造size
        size = packageName if packageName != None and sizeName == None else sizeName
        if hasStyle : size+='_{style}'.format(style=styleName) if size else styleName
        if hasEdition : size+='_{edition}'.format(edition=editionName) if size else editionName
        if not size : size=inst.cfg.DEFAULT_ONE_SIZE

        #构造color
        if not colorName and editionName :       #有版本没有颜色. 针对电玩.
            colorName = editionName
        elif styleName and colorName :
            colorName = styleName + ' ' + colorName
        elif styleName :
            colorName = styleName
        elif not colorName : 
            colorName = inst.cfg.DEFAULT_ONE_COLOR

        link = blink +'&psc={psc}&asinList={asinList}&isFlushing={isFlushing}&dpEnvironment={dpEnvironment}&id={id}&mType={mType}'.format(psc=1,asinList=asin,isFlushing=2,dpEnvironment=dpEnvironment,id=asin,mType='full')

        #构造数据,库存默认为0,价格为0，原价为0.
        sizeObj=dict(asin=asin,id=asin,sku=asin,link=link,name=size,inventory=0,price=0,listPrice=0)

        #amazon 不获取详细库存固定库存为1
        # sizeObj=dict(sku=asin,size=size,inventory=1)

        # print '+++++++++++++++++++++++++++++',colorName,sizeObj

        if colorName in color_asins:
            color_asins[colorName].append(sizeObj)
        elif colorName not in color_asins :
            color_asins[colorName]=[sizeObj]

    return color_asins

def nowait_distill(inst,leftCol,rightCol,centerCol,pqhtml):
    unit,currency =  amazon_unit(inst.url)
    imgsData =  amazon_general_imgs(leftCol,pqhtml)

    data =  amazon_general_info_nowait(inst,pqhtml)

    if data and isinstance(data,dict) :
        name=data['names'] if data['names'] else  amazon_general_name(centerCol)
        sizes=data['sizes'] if data['sizes'] else ''
        brand=data['brands'] if data['brands'] else  amazon_general_brand(centerCol)
        descr=data['descrs'] if data['descrs'] else  amazon_general_descr(centerCol,pqhtml)
        price=data['prices'] if data['prices'] else  amazon_general_price(centerCol)
        listPrice=data['oldPrices'] if data['oldPrices'] else  amazon_general_oldPrice(centerCol)
    else :
        name= amazon_general_name(centerCol)
        sizes= amazon_general_oneSize(inst,centerCol,rightCol)
        brand= amazon_general_brand(centerCol)
        descr= amazon_general_descr(centerCol,pqhtml)
        price= amazon_general_price(centerCol)
        listPrice= amazon_general_oldPrice(centerCol)

    returns = ''
    designer = ''

    color = dict([(k,k) for k in sizes]) if isinstance(sizes,dict) else  inst.cfg.DEFAULT_ONE_COLOR

    imgs =  amazon_convert_imgKey(inst,sizes,imgsData)      #传入实例

    productId = pqhtml('form#addToCart input[name="ASIN"]').attr('value')


    detail = dict()

    detail['brand'] = brand
    detail['name'] = name
    detail['currency'] = currency
    detail['currencySymbol'] = unit
    detail['price'] = price
    detail['listPrice'] = listPrice
    detail['color'] = color
    detail['colorId'] = dict([(key,key) for key in color.keys() ]) if isinstance(color,dict) else productId
    detail['img'] = dict([(key,imgArr[0]) for key,imgArr in imgs.items() ]) if isinstance(color,dict) else imgs[0]
    detail['imgs'] = imgs
    detail['productId'] = productId
    detail['sizes'] = sizes
    detail['descr'] = descr
    
    #多颜色
    if isinstance(sizes,dict) :
        detail['keys'] = sizes.keys()

    #需要延时获取？
    inst.need_wait = False

    return detail


def amazon_general_info_nowait(inst,pqhtml):
    #获取一个参数:
    environmentTxt = None
    for i,ele in enumerate(pqhtml('#twisterJsInitializer_feature_div script').items()):
        # print i
        # print ele.text()
        if 'dpEnvironment' in ele.text() :
            environmentTxt = ele.text()
    # print environmentTxt
    #获取参数数据DATA
    if environmentTxt :
        r = re.search(r'\s*var\s*(dataToReturn =.*?);\s*return dataToReturn;',environmentTxt,re.DOTALL)
        if r :
            null=None
            true=True
            false=False
            exec r.groups()[0]
            dpxData=dataToReturn
            # print json.dumps(dpxData)
            dpEnvironment=dpxData['dpEnvironment']
        else :
            raise ValueError,'get dpEnvironment Fail'
    else :
        dpEnvironment='hardlines'
        # print '+++++++Warning: Get dpEnvironment Fail'
        return None

    #判断页面数据位置
    for i,ele in enumerate(pqhtml('script').items()):
        # print i
        # print ele.outerHtml()
        if 'useTwisterJsInitFromDPXPartially' in ele.text() :
            dataToReturnTxt = ele.text()
            break
    else :
        raise ValueError,'search dataToReturn Fail'

    dataToReturnTxt = dataToReturnTxt.replace('//selectively not escaping this.','')
    #获取页面数据JSON
    r = re.search(r'\s*var\s*(dataToReturn =.*?);\s*return dataToReturn;',dataToReturnTxt,re.DOTALL)
    if r :
        null=None
        true=True
        false=False
        exec r.groups()[0]

        data =  amazon_general_dataToReturn_nowait(inst,dataToReturn,dpEnvironment)
        return data
    else :
        raise ValueError,'get dataToReturn Fail'

    raise ValueError,'Get Sizes Fail'


def amazon_general_oneSize(inst,centerCol,rightCol):

    buybox=rightCol('#buybox_feature_div')

    if not buybox :
        buybox = centerCol('#buybox_feature_div')

    if not buybox:
        buybox = inst.pqhtml('#buybox_feature_div')

    inv = buybox('select#quantity>option:last').attr('value')

    if not inv :
        t = centerCol('#availability_feature_div #availability').text()
        g = re.search(r'(\d)',t)
        if g : 
            inv = g.groups()[0]
        elif 'in stock' in t.lower() :
            inv = inst.cfg.DEFAULT_STOCK_NUMBER
        else:
            inv = 0
    asin = buybox('input#ASIN').attr('value')

    return [dict(name= inst.cfg.DEFAULT_ONE_SIZE,inventory=inv,sku=asin,id=asin)]


def amazon_general_dataToReturn_nowait(inst,dataToReturn,dpEnvironment):

    # print json.dumps(dataToReturn)
    # 判断页面都有哪些尺码
    displayLabels = dataToReturn['variationDisplayLabels']
    hasSize='size_name' in displayLabels
    hasColor='color_name' in displayLabels
    hasStyle='style_name' in displayLabels
    hasEdition='edition' in displayLabels
    hasPackage='customer_package_type' in displayLabels

    # 尺码对应的值数组
    variation_values=dataToReturn['variation_values']
    size_name=variation_values['size_name'] if hasSize else None
    color_name=variation_values['color_name'] if hasColor else None
    style_name=variation_values['style_name'] if hasStyle else None
    edition_name=variation_values['edition'] if hasEdition else None
    package_name=variation_values['customer_package_type'] if hasPackage else None

    #获取库存条件
    params=dataToReturn['twisterUpdateURLInfo']['immutableParams']
    dlink= inst.domain+dataToReturn['twisterUpdateURLInfo']['immutableURLPrefix'].split('?')[0]
    blink= inst.domain+dataToReturn['twisterUpdateURLInfo']['immutableURLPrefix']

    #其他参数
    contextMetaData=dataToReturn['contextMetaData']
    params.update(contextMetaData['full']['mTypeSpecificURLParams'])
    params.update(contextMetaData['parent']['mTypeSpecificURLParams'])
    params.update(contextMetaData['master']['mTypeSpecificURLParams'])
    params.update(contextMetaData['partial']['mTypeSpecificURLParams'])
    params['dpEnvironment']=dpEnvironment

    # print json.dumps(params)

    #构造数据
    sizes={}
    names={}
    descrs={}
    brands={}
    prices={}
    oldPrices={}
    asin_to_values = dataToReturn['asin_variation_values']
    for asin,item in asin_to_values.items() :
        sizeName = size_name[int(item['size_name'])] if hasSize else ''
        colorName = color_name[int(item['color_name'])] if hasColor else ''
        styleName = style_name[int(item['style_name'])] if hasStyle else ''
        editionName = edition_name[int(item['edition'])] if hasEdition else ''
        packageName = package_name[int(item['customer_package_type'])] if hasPackage else ''

        #构造size
        size = packageName if packageName != None and sizeName == None else sizeName
        if hasStyle : size+='_{style}'.format(style=styleName) if size else styleName
        if hasEdition : size+='_{edition}'.format(edition=editionName) if size else editionName
        if not size : size= inst.cfg.DEFAULT_ONE_SIZE

        #构造color
        if not colorName and editionName :       #有版本没有颜色. 针对电玩.
            colorName = editionName
        elif styleName and colorName :
            colorName = styleName + ' ' + colorName
        elif styleName :
            colorName = styleName
        elif not colorName : 
            colorName =  inst.cfg.DEFAULT_ONE_COLOR

    #获取详细库存
        pparams=params.copy()
        pparams['qid']=str(int(time.time()))
        pparams['id'] = asin
        pparams['asinList'] = asin
        pparams['isFlushing'] = '2'
        pparams['mType'] = 'full'
        pparams['psc'] = '1'
        pparams['isOC'] = '1'

        # response= session.get(dlink,params=params, verify=False)

        link = blink +'&psc={psc}&asinList={asinList}&isFlushing={isFlushing}&dpEnvironment={dpEnvironment}&id={id}&mType={mType}'.format(psc=1,asinList=asin,isFlushing=2,dpEnvironment=dpEnvironment,id=asin,mType='full')
        # response= Get(blink,headers= get_One_headers())

        response= inst.session.get(link, verify=False)
        # print time.clock()

        if response.content.strip()[:2]=='{}' :
            print '+++++++++++++++++Warning :',link,'\n\n\n'

        # print response.content


        data= amazon_general_asinDetail_nowait(response)

        #构造数据
        sizeObj=dict(size=size,sku=asin,inventory=data['inv'],price=data['price'],oldPrice=data['oldPrice'])

        # print '+++++++++++++++++++++++++++++',colorName,sizeObj

        if colorName in sizes:
            sizes[colorName].append(sizeObj)
        elif colorName not in sizes :
            sizes[colorName]=[sizeObj]
        # elif colorName not in sizes and not data['inv'] :
        #     sizes[colorName]=''

        if data['name'] and colorName not in names : names[colorName]=data['name']
        if data['brand'] and colorName not in brands : brands[colorName]=data['brand']
        if data['price'] and colorName not in prices : prices[colorName]=data['price']
        if data['descr'] and colorName not in descrs : descrs[colorName]=data['descr']
        if data['oldPrice'] and colorName not in oldPrices : oldPrices[colorName]=data['oldPrice']

    return dict(sizes=sizes,names=names,descrs=descrs,brands=brands,prices=prices,oldPrices=oldPrices)


def amazon_general_asinDetail_nowait(response):
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


def amazon_general_descr(centerCol,pqhtml):
    # print centerCol.outerHtml()
    # print pqhtml.outerHtml()
    descr = centerCol('#featurebullets_feature_div').remove('script').text() or ''
    descr += (pqhtml('#productDescription').remove('script').text() or '')

    if not descr :
        for ele in pqhtml('script[type="text/javascript"]').items() :
            if 'ProductDescriptionIframeResize' in ele.text() :
                descr = re.search(r'var iframeContent = "(.*)";\n',ele.text()).groups()[0]
                descr = PyQuery(urllib.unquote(descr))
                descr.remove('script')
                descr = descr('#productDescription').text()
                break
        else :
            raise ValueError,'Get Descr Fail'            
    
    return descr 


def amazon_general_oldPrice(centerCol):
    if len(centerCol('#price tr')) > 1 :
        price = centerCol('#price tr:first>td:last').text()
    else :
        price = centerCol('#priceblock_ourprice').text()           #第一种方式
        if not price : price = centerCol('#priceblock_dealprice').text()        #第二种方式
        if not price : price = centerCol('#priceblock_saleprice').text()        #第三种方式
        if not price : price = centerCol('#olp_feature_div .a-color-price').text()        #第四种方式

    if price :
        price = price.replace(',','')
        price = re.search(r'(\d[\.\d]*)',price,re.DOTALL).groups()[0].strip()
        return price

    return 0


def amazon_general_price(centerCol):
    price = centerCol('#priceblock_ourprice').text()        #第一种方式
    if not price : price = centerCol('#priceblock_dealprice').text()        #第二种方式
    if not price : price = centerCol('#priceblock_saleprice').text()        #第三种方式
    if not price : price = centerCol('#olp_feature_div .a-color-price').text()        #第四种方式

    if price :
        price = price.replace(',','')
        price = re.search(r'(\d[\.\d]*)',price,re.DOTALL).groups()[0].strip()
        return price

    return 0


def amazon_general_brand(centerCol):

    ele=centerCol('a#brand')

    brand = ele.text() or centerCol('a#brandteaser img').attr('alt')

    if not brand and ele :
        brand=ele.attr('href').split('/')[1]

    if not brand :

        raise ValueError,'Get Brand Fail'
    
    return brand


def amazon_general_name(centerCol):
    name=centerCol('h1#title').text()

    if name :
        return name

    raise ValueError,'Get Name Fail'


def amazon_general_imgs(leftCol,pqhtml):
    # print pqhtml.outerHtml()
    null=None
    false=False
    true=True
    data=None
    #判断图片数据位置
    for i,ele in enumerate(pqhtml('.a-container>script').items()):
        if 'register(\'ImageBlockBTF\'' in ele.text() :
            JscriptTxt = ele.text()
            # print JscriptTxt
            r = re.search(r'\s*data\["colorImages"\] =(.*?)\s*data\["heroImage"\]',JscriptTxt,re.DOTALL)
            if r :
                exec 'data='+r.groups()[0]
                # print '==========================',data
                break

    if not data :            
        for i,ele in enumerate(leftCol('script').items()):
            if 'register("ImageBlockATF"' in ele.text() :
                JscriptTxt = ele.text()
                r = re.search(r'var\s*(data =.*?\});',JscriptTxt,re.DOTALL)
                if r : 
                    exec r.groups()[0]
                break
        else :
            raise ValueError,'search IMG Data Fail'

    if not data :
        raise ValueError,'get IMG Data Fail'

    # print json.dumps(data)
    # imgs = dict([(cname.decode('utf-8'),[a.get('hiRes',a.get('large',a.get('thumb'))) for a in arr]) for cname,arr in data.items()])

    try:
        imgs = dict([(cname,[a.get('hiRes',a.get('large',a.get('thumb'))) for a in arr]) for cname,arr in data.items()])
    except (TypeError,AttributeError):
        if isinstance(data['colorImages'],dict) and len(data['colorImages'].keys()) == 1 :
            imgs = [a['hiRes'] or a['large'] or a['thumb'] for a in data['colorImages']['initial'] ]
        else :
            raise

    # print json.dumps(imgs)
    if imgs :
        return imgs

    raise ValueError,'Get Imgs Fail'