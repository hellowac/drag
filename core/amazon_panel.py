#coding:utf-8

from .amazon_util import amazon_unit,amazon_convert_imgKey
from .amazon_general import amazon_general_oneSize, amazon_general_imgs, amazon_general_name, amazon_general_descr, amazon_general_price, amazon_general_oldPrice, amazon_general_brand, amazon_general_info_wait

def distill(inst,leftCol,actionPanel,pqhtml):

    unit,currency = amazon_unit(inst.url)
    imgsData = amazon_general_imgs(leftCol,pqhtml)

    #不发ajax获取详细信息.
    sizes = amazon_general_info_wait(inst,pqhtml)

    if not sizes : 
        sizes = amazon_panel_oneSize(inst,actionPanel,actionPanel)
        #需要延时获取？
        inst.need_wait = False

    else :
        inst.need_wait = True

    name=amazon_panel_name(leftCol)
    brand=amazon_panel_brand(leftCol)
    descr=amaozn_panel_descr(leftCol,pqhtml)
    price=amazon_panel_price(actionPanel)
    listPrice=amazon_panel_oldPrice(actionPanel)

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
    detail['colorId'] = dict([(key,key) for key in color.keys() ]) if isinstance(color,dict) else productId
    detail['img'] = dict([(key,imgArr[0]) for key,imgArr in imgs.items() ]) if isinstance(color,dict) and isinstance(imgs, dict) else imgs[0]
    detail['imgs'] = imgs
    detail['productId'] = productId
    detail['sizes'] = sizes
    detail['descr'] = descr
    
    #多颜色
    if isinstance(sizes,dict) :
        detail['keys'] = sizes.keys()

    return detail


def amazon_panel_oneSize(inst,centerCol,actionPanel):

    return amazon_general_oneSize(inst,centerCol,actionPanel)


def amazon_panel_imgs(inst,leftCol,pqhtml):

    return amazon_general_imgs(leftCol,pqhtml)


def amazon_panel_name(leftCol):

    return amazon_general_name(leftCol)

    
def amaozn_panel_descr(leftCol,pqhtml):

    return amazon_general_descr(leftCol,pqhtml)


def amazon_panel_price(actionPanel):

    return amazon_general_price(actionPanel)


def amazon_panel_oldPrice(actionPanel):

    return amazon_general_oldPrice(actionPanel)


def amazon_panel_brand(leftCol):

    return amazon_general_brand(leftCol)


def amaozn_panel_info(pqhtml):

    return amazon_general_info(pqhtml)
