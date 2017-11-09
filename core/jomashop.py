#!/usr/bin/python
#coding:utf-8
__author__ = 'wangchao'
__status__ = "product"
__version__ = "0.1"
__date__ = "2016/07/04"

#0.1 初始版
from . import DragBase
from pyquery import PyQuery
from utils import tool
import re
import json
import time
import random
import urllib


class Drag(DragBase, object):

    def __init__(self, cfg):
        super(Drag, self).__init__(cfg)


    #获取页面大概信息
    def multi(self, url):
        pass


    #获取详细信息
    def detail(self,url):
        try:

            resp = self.session.get(url, verify=False)

            #这两行代码为验证做准备,勿动.
            self.domain = tool.get_domain(url)
            self.url = url

            #验证resp
            resp = self.resVerify(resp)

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

            #前期准备:
            area = pqhtml('.product-view')
            productId = area('.product-ids').attr('content')
            pdata = self.get_pdata(pqhtml)

            # print pqhtml.outerHtml()
            # print area.outerHtml()
            # print json.dumps(pdata)
            # exit()

            #下架
            if not len(PyQuery(pdata['availability'])('.instock')) :

                log_info = json.dumps(dict(time=time.time(),title=pqhtml('title').text(),url=url))

                self.logger.info(log_info)

                data = tool.get_off_shelf(code=status_code,message=self.cfg.SOLD_OUT,backUrl=resp.url, html=pqhtml.outerHtml())
                return tool.return_data(successful=False, data=data)

            detail = dict()

            #品牌
            brand = pdata['brand']
            detail['brand'] = brand

            #名称
            detail['name'] = brand + ' ' + pdata['title']

            #货币单位
            currency = pqhtml('meta[itemprop="priceCurrency"]').attr('content')
            detail['currency'] = currency
            detail['currencySymbol'] = tool.get_unit(currency)

            #价格
            price,listPrice = self.get_all_price(pdata)
            detail['price'] = price
            detail['listPrice'] = listPrice

            #描述
            detail['descr'] = pqhtml('div.product-description').text()

            #颜色
            detail['color'] = self.cfg.DEFAULT_ONE_COLOR
            detail['colorId'] = pdata['sku']

            #图片集
            detail['img'] = pdata['image']
            detail['imgs'] = pdata['images']

            #规格
            detail['sizes'] = [dict(name=self.cfg.DEFAULT_ONE_SIZE,inventory=self.cfg.DEFAULT_STOCK_NUMBER,sku=pdata['sku'])]

            #产品ID
            detail['productId'] = pdata['sku']

            #退换货
            detail['returns'] = pqhtml('dd#tab-container-guarantee').text()

            #HTTP状态码
            detail['status_code'] = status_code

            #状态
            detail['status'] = self.cfg.STATUS_SALE

            #返回链接
            detail['backUrl'] = url
            
            log_info = json.dumps(dict(time=time.time(), productId=detail['productId'], name=detail[
                                  'name'], currency=detail['currency'], price=detail['price'], listPrice=detail['listPrice'], url=url))

            self.logger.info(log_info)

            return tool.return_data(successful=True, data=detail)

        except Exception, e:
            raise

    #验证函数
    def resVerify(self,resp):
        pqhtml = PyQuery(resp.text)

        # print pqhtml.outerHtml()

        if 'NOINDEX, NOFOLLOW' in (pqhtml('meta[name="ROBOTS"]').attr('content') or '') :
            src = self.domain + pqhtml('script[defer="defer"]').attr('src')

            # print('ban src :{}'.format(src))
            resp = self.session.get(src, verify=False)

            postUrl = self.domain + resp.headers.get('X-JU')
            postKey = resp.headers.get('X-AH')

            self.session.headers['X-Distil-Ajax'] = postKey

            ua = self.session.headers.get('User-Agent')

            postData = self.get_verifyData(ua)

            postData = dict(p=urllib.quote(json.dumps(postData)))

            resp = self.session.post(postUrl,data=postData)

            self.session.headers.pop('X-Distil-Ajax')

            resp=self.session.get(self.url, verify=False)

        return resp

    #验证需要发送的数据
    def get_verifyData(self,ua):
        
        timeStr = str(int(time.time()*1000))
        key1 = ''.join([random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for i in range(random.choice([2,3]))])
        key2 = ''.join([random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for i in range(20)])


        data = {
            # "proof": "1bb:1469587482050:dCL3J89EgaMGsRtsU4Qf",
            "proof":':'.join([key1,timeStr,key2]),
            "fp2": {
                "userAgent": ua,
                "language": "zh-CN",
                "screen": {
                    "width": 1920,
                    "height": 1080,
                    "availHeight": 1052,
                    "availWidth": 1920
                },
                "timezone": 8,
                "indexedDb": True,
                "addBehavior": False,
                "openDatabase": True,
                "cpuClass": "unknown",
                "platform": "Win32",
                "doNotTrack": "unknown",
                "plugins": "ChromePDFViewer::::application/pdf~pdf;ChromePDFViewer::PortableDocumentFormat::application/x-google-chrome-pdf~pdf;NativeClient::::application/x-nacl~,application/x-pnacl~;ShockwaveFlash::ShockwaveFlash22.0r0::application/x-shockwave-flash~swf,application/futuresplash~spl;WidevineContentDecryptionModule::EnablesWidevinelicensesforplaybackofHTMLaudio/videocontent.(version:1.4.8.903)::application/x-ppapi-widevine-cdm~",
                "canvas": {
                    "winding": "yes",
                    "towebp": True,
                    "blending": True,
                    "img": "bee2268196da07b3a5452baecdb69817689bfe04"
                },
                "webGL": {
                    "img": "ec1ac927598cc32e395530f37437b13e3d7a4bdc",
                    "extensions": "ANGLE_instanced_arrays;EXT_blend_minmax;EXT_disjoint_timer_query;EXT_frag_depth;EXT_shader_texture_lod;EXT_sRGB;EXT_texture_filter_anisotropic;WEBKIT_EXT_texture_filter_anisotropic;OES_element_index_uint;OES_standard_derivatives;OES_texture_float;OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;OES_vertex_array_object;WEBGL_compressed_texture_etc1;WEBGL_compressed_texture_s3tc;WEBKIT_WEBGL_compressed_texture_s3tc;WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;WEBKIT_WEBGL_depth_texture;WEBGL_draw_buffers;WEBGL_lose_context;WEBKIT_WEBGL_lose_context",
                    "aliasedlinewidthrange": "[1,1]",
                    "aliasedpointsizerange": "[1,1024]",
                    "alphabits": 8,
                    "antialiasing": "yes",
                    "bluebits": 8,
                    "depthbits": 24,
                    "greenbits": 8,
                    "maxanisotropy": 16,
                    "maxcombinedtextureimageunits": 32,
                    "maxcubemaptexturesize": 16384,
                    "maxfragmentuniformvectors": 1024,
                    "maxrenderbuffersize": 16384,
                    "maxtextureimageunits": 16,
                    "maxtexturesize": 16384,
                    "maxvaryingvectors": 30,
                    "maxvertexattribs": 16,
                    "maxvertextextureimageunits": 16,
                    "maxvertexuniformvectors": 1024,
                    "maxviewportdims": "[16384,16384]",
                    "redbits": 8,
                    "renderer": "WebKitWebGL",
                    "shadinglanguageversion": "WebGLGLSLES1.0(OpenGLESGLSLES1.0Chromium)",
                    "stencilbits": 0,
                    "vendor": "WebKit",
                    "version": "WebGL1.0(OpenGLES2.0Chromium)",
                    "vertexshaderhighfloatprecision": 23,
                    "vertexshaderhighfloatprecisionrangeMin": 127,
                    "vertexshaderhighfloatprecisionrangeMax": 127,
                    "vertexshadermediumfloatprecision": 23,
                    "vertexshadermediumfloatprecisionrangeMin": 127,
                    "vertexshadermediumfloatprecisionrangeMax": 127,
                    "vertexshaderlowfloatprecision": 23,
                    "vertexshaderlowfloatprecisionrangeMin": 127,
                    "vertexshaderlowfloatprecisionrangeMax": 127,
                    "fragmentshaderhighfloatprecision": 23,
                    "fragmentshaderhighfloatprecisionrangeMin": 127,
                    "fragmentshaderhighfloatprecisionrangeMax": 127,
                    "fragmentshadermediumfloatprecision": 23,
                    "fragmentshadermediumfloatprecisionrangeMin": 127,
                    "fragmentshadermediumfloatprecisionrangeMax": 127,
                    "fragmentshaderlowfloatprecision": 23,
                    "fragmentshaderlowfloatprecisionrangeMin": 127,
                    "fragmentshaderlowfloatprecisionrangeMax": 127,
                    "vertexshaderhighintprecision": 0,
                    "vertexshaderhighintprecisionrangeMin": 31,
                    "vertexshaderhighintprecisionrangeMax": 30,
                    "vertexshadermediumintprecision": 0,
                    "vertexshadermediumintprecisionrangeMin": 31,
                    "vertexshadermediumintprecisionrangeMax": 30,
                    "vertexshaderlowintprecision": 0,
                    "vertexshaderlowintprecisionrangeMin": 31,
                    "vertexshaderlowintprecisionrangeMax": 30,
                    "fragmentshaderhighintprecision": 0,
                    "fragmentshaderhighintprecisionrangeMin": 31,
                    "fragmentshaderhighintprecisionrangeMax": 30,
                    "fragmentshadermediumintprecision": 0,
                    "fragmentshadermediumintprecisionrangeMin": 31,
                    "fragmentshadermediumintprecisionrangeMax": 30,
                    "fragmentshaderlowintprecision": 0,
                    "fragmentshaderlowintprecisionrangeMin": 31,
                    "fragmentshaderlowintprecisionrangeMax": 30
                },
                "touch": {
                    "maxTouchPoints": 0,
                    "touchEvent": True,
                    "touchStart": True
                },
                "video": {
                    "ogg": "probably",
                    "h264": "probably",
                    "webm": "probably"
                },
                "audio": {
                    "ogg": "probably",
                    "mp3": "probably",
                    "wav": "probably",
                    "m4a": "maybe"
                },
                "fonts": "Batang;Calibri;Century;Haettenschweiler;Leelawadee;Marlett;PMingLiU;Pristina;Vrinda"
            },
            "cookies": 1,
            "setTimeout": 0,
            "setInterval": 0,
            "appName": "Netscape",
            "platform": "Win32",
            "syslang": "zh-CN",
            "userlang": "zh-CN",
            "cpu": "",
            "productSub": "20030107",
            "plugins": {
                "0": "WidevineContentDecryptionModule",
                "1": "ShockwaveFlash",
                "2": "ChromePDFViewer",
                "3": "NativeClient",
                "4": "ChromePDFViewer"
            },
            "mimeTypes": {
                "0": "WidevineContentDecryptionModuleapplication/x-ppapi-widevine-cdm",
                "1": "ShockwaveFlashapplication/x-shockwave-flash",
                "2": "ShockwaveFlashapplication/futuresplash",
                "3": "application/pdf",
                "4": "NativeClientExecutableapplication/x-nacl",
                "5": "PortableNativeClientExecutableapplication/x-pnacl",
                "6": "PortableDocumentFormatapplication/x-google-chrome-pdf"
            },
            "screen": {
                "width": 1920,
                "height": 1080,
                "colorDepth": 24
            },
            "fonts": {
                "0": "Calibri",
                "1": "Cambria",
                "2": "Times",
                "3": "Constantia",
                "4": "LucidaBright",
                "5": "Georgia",
                "6": "SegoeUI",
                "7": "Candara",
                "8": "TrebuchetMS",
                "9": "Verdana",
                "10": "Consolas",
                "11": "LucidaConsole",
                "12": "LucidaSansTypewriter",
                "13": "DejaVuSansMono",
                "14": "CourierNew",
                "15": "Courier"
            }
        }

        return data


    def get_all_price(self,pdata):
        ptxt = pdata['price'].replace(',','')
        price = re.search(r'(\d[\d\.]+)',ptxt).groups()[0]

        ptxt = pdata['retail'].replace(',','')
        listPrice = re.search(r'(\d[\d\.]+)',ptxt).groups()[0]

        if not price or not listPrice :
            raise Exception('Get price or listPrice fail, price:%s listPrice:%S' %(price,listPrice))

        return price,listPrice

    def get_pdata(self,pqhtml):

        productId = pqhtml('.product-ids').attr('content')

        data = None

        for ele in pqhtml('script[type="text/javascript"]').items():

            if 'xItemArray' in ele.text() :
                data = re.search(r'xItemArray = (.+);$',ele.text(),re.DOTALL).groups()[0]
                break
        else :
            raise Exception('Get itemArray fault')

        jdata = json.loads(data)
        return jdata['xitems'][jdata['primary_item']]


