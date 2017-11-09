#!/usr/bin/python
#coding:utf-8

import re
from .amazon_util import amazon_unit

def distill(inst,leftCol,rightCol,centerCol,pqhtml):
    unit,currency = amazon_unit(inst.url)
    imgs = amazon_book_imgs(leftCol)
    name = amazon_book_name(centerCol)
    brand = amazon_book_brand(pqhtml)
    price = amazon_book_price(centerCol)
    descr = amazon_book_descr(centerCol)
    sizes = amazon_book_sizes(centerCol,rightCol)
    color = inst.cfg.DEFAULT_ONE_COLOR
    listPrice = amazon_book_oldPrice(rightCol)
    designer = amazon_book_author(centerCol)
    productId = pqhtml('#addToCart input[name="ASIN"]').attr('value')

    detail = dict()

    detail['brand'] = brand
    detail['name'] = name
    detail['currency'] = currency
    detail['currencySymbol'] = unit
    detail['price'] = price
    detail['listPrice'] = listPrice
    detail['color'] = color
    detail['colorId'] = productId
    detail['img'] = imgs[0]
    detail['imgs'] = imgs
    detail['productId'] = productId
    detail['sizes'] = sizes
    detail['descr'] = descr

    #需要延时获取？
    inst.need_wait = False

    return detail

def amazon_book_brand(pqhtml):
    detail = pqhtml('#detail_bullets_id .content ul>li')

    detail.remove('script')

    for ele in detail.items() :
        if u'品牌' in ele.text() :
            return ele.text().split(':')[1]
    else :
        return ''

    raise ValueError,'Get Brand Fail'
    
def amazon_book_author(centerCol):
    designer = centerCol('.author').text()
    if designer :
        return designer

    raise ValueError,'Get designer Fail'

def amazon_book_sizes(centerCol,rightCol):
    table = centerCol('#MediaMatrix div.selected-row table')
    title = table('.dp-title-col .title-text').text()
    inv = rightCol('form#addToCart #quantity>option:last').attr('value')
    asin = rightCol('form#addToCart input#ASIN').attr('value')

    if title and inv :
        return [{'name':title,'inventory':inv,'sku':asin,'id':asin}]

    raise ValueError,'Get Book Size Fail'

def amazon_book_oldPrice(rightCol):
    oldPrice = rightCol('form #buybox #buyNewInner>#buyBoxInner span>.a-color-secondary').text()
    if oldPrice :
        return re.search(r'(\d[\.\d]*)',oldPrice,re.DOTALL).groups()[0]

    raise ValueError,'Get book oldPrice Fail'

def amazon_book_price(centerCol):
    MediaMatrix=centerCol('#MediaMatrix #tmmSwatches li.selected')
    price = MediaMatrix('.a-color-price').text()

    if price :
        return re.search(r'(\d[\.\d]*)',price,re.DOTALL).groups()[0]

    raise ValueError,'Get book price Fail'

def amazon_book_descr(centerCol):
    descr = centerCol('#bookDescription_feature_div noscript').text()

    if descr :
        return descr

    raise ValueError,'Get book descr Fail'

def amazon_book_name(centerCol):
    name = centerCol('#productTitle').text()
    if name :
        return name

    raise ValueError,'Get book Name Fail'

def amazon_book_imgs(leftCol):
    JscriptTxt = leftCol('script').text()

    r = re.search(r'var\s*(data =\s*\{.*?\});',JscriptTxt,re.DOTALL)

    if r :
        none=None
        true=True
        false=False
        audibleData = None
        exec r.groups()[0]

        return [img['mainUrl'] for img in data['imageGalleryData']]

    raise ValueError,'Get book Imgs Fail'
