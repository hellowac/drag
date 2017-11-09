# coding:utf-8

import os
import time
import logging
import ConfigParser
from logging import handlers


pro_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cfgName =   os.path.join(pro_dir, 'conf', 'config.conf')

config = ConfigParser.RawConfigParser()
config.read(cfgName)


def get_os_info():
    import uuid
    import platform

    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    mac_addr = ':'.join([mac[e:e+2] for e in range(0, 11, 2)])
    sysType = platform.system()

    return sysType, mac_addr


basedir = os.path.abspath(os.path.dirname(__file__))

sysType, mac_addr = get_os_info()


class BaseCfg: 
    REQUEST_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 "
        "(KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 "
        "(KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 "
        "(KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 "
        "(KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 "
        "(KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 "
        "(KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 "
        "(KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 "
        "(KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 "
        "(KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 "
        "(KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
    ]

    REQUEST_ACCEPT_LANGUAGE = [
        "zh-CN", "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3", "zh-CN,zh;q=0.8,en;q=0.6"]

    # 特殊的渠道名称
    SPICAL_CHANNEL_NAMES = {'6pm':'sixpm',
                            'oki-ni':'okini',
                            'native-youth':'nativeyouth',}

    # 图片存储路径
    STORE_IMG_PATH = {'Linux': '/var/log/drag/img/',
                      'Windows': os.path.join(basedir, 'imgs'),
                      'Darwin':'/var/log/drag/img/'}[sysType]

    # 图片访问路径
    REQUEST_IMG_PATH = {
        'Darwin': 'http://127.0.0.1:5000/downImg/',
    }[sysType]

    LOG_PATH = config.get('log', 'drag_path')

    #创建日志目录
    # if not os.path.exists(LOG_PATH) :
    #     os.makedirs(LOG_PATH)

    #日志文件名.
    LOG_GENERALFILE = 'general.log'

    #日志异常文件名
    LOG_EXCEPTIONFILE = 'exception.log'

    #日志信息格式
    LOG_FMT = '%(asctime)-15s %(levelname)s  {"time":"%(asctime)-15s","levelname":"%(levelname)s","Line number" : "%(lineno)d", "message": %(message)s}'

    #日志日期格式
    LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"

    #日志分割后缀
    LOG_SUFFIX = "%Y%m%d.log"

    #日志处理者
    # LOGGER = tool.Logger

    STORE_COOKIES_PATH = os.environ.get('DRAG_COOKIES_PATH')

    # 启用cookie?
    USE_COOKIES = False

    #cookieJar
    COOKIEJAR = None

    #是否启用代理
    USE = dict(
        PROXY = False,              #默认不起用代理
        PROXY_TYPE = 'GENERAL',     #默认常规代理,另外一种 SOCKS,FREEPROXY
    )    

    PROXIES = {

        # 普通代理
        'GENERAL':{
            'http': 'http://solideo:WWonly31031@us-fl.proxymesh.com:31280'
        },

        # socks代理,requests 版本必须大于等于 2.10.0 ,否则使用的版本为requesocks.
        'SOCKS': {
            "http": 'socks5://127.0.0.1:1080',
            "https": 'socks5://127.0.0.1:1080',
        }
    }

    #连接最大尝试次数
    MAX_RETRIES = 5

    #超时设置.10 minutes
    REQUEST_TIME_OUT = 10

    DEFAULT_STOCK_NUMBER = 10

    DEFAULT_ONE_COLOR = 'No Info'

    DEFAULT_ONE_SIZE = 'One Size'

    DEFAULT_SIZE_SKU = '001'

    DEFAULT_COLOR_SKU = '001'

    DEFAULT_PRODUCT_SKU = '001'

    #默认下架标识
    SOLD_OUT = 'Sold Out'

    #默认错误标识
    GET_ERR = {
                'SCERR':'Status_code Error',                    #状态码错误
                'NTFOUND':'404 error',                          #页面not found 错误
                'NTONLINE':'not sale for online',               #不在线上销售
                'DOMAINERR':'url\'s domain error',              #url中域名错误
                'LUIPERR':'luisaviaroma pricing is none error', #luisaviaroma 会出现不返回价格情况.
                'SAKERR':'saksoff5th page error'                #saksoff5th 返回页面错误.
              }

    #状态标识
    STATUS_SALE='sale'           #现货
    STATUS_SOUT='stock out'      #缺货
    STATUS_ERROR='error'         #错误
    STATUS_PRESELL='presell'     #预售
    STATUS_OFFSHELF='off shelf'  #下架

def get_logger():

        #格式者
        formatter = logging.Formatter(BaseCfg.LOG_FMT, BaseCfg.LOG_DATEFMT)

        logFile = os.path.join(BaseCfg.LOG_PATH,BaseCfg.LOG_GENERALFILE)

        #处理者,常规日志文件
        gHandler = handlers.TimedRotatingFileHandler(logFile, 'D', 1, 0)
        gHandler.setFormatter(formatter)
        gHandler.setLevel(logging.INFO)
        gHandler.suffix = BaseCfg.LOG_SUFFIX
        gHandler = logging.FileHandler(os.path.join(BaseCfg.LOG_PATH,BaseCfg.LOG_GENERALFILE))
        gHandler.setLevel(logging.DEBUG)
        gHandler.setFormatter(formatter)

        #处理者,异常日志文件
        eHandler = handlers.TimedRotatingFileHandler(os.path.join(BaseCfg.LOG_PATH,BaseCfg.LOG_EXCEPTIONFILE), 'D', 1, 0)
        eHandler.setFormatter(formatter)
        eHandler.setLevel(logging.ERROR)
        eHandler.suffix = BaseCfg.LOG_SUFFIX
        eHandler = logging.FileHandler(os.path.join(BaseCfg.LOG_PATH,BaseCfg.LOG_EXCEPTIONFILE))
        eHandler.setLevel(logging.ERROR)
        eHandler.setFormatter(formatter)

        #记录器
        logger = logging.getLogger('Draglog')
        logger.setLevel(logging.DEBUG)

        logger.addHandler(gHandler)
        logger.addHandler(eHandler)

        return logger

class InstanceCfg(object,BaseCfg):

    #错误追踪字段
    ERROR_ATTR = [
        'status',            #状态
        'html',             #html文档
        'title',            #文档标题
        'backUrl',          #返回链接
        'status_code',      #返回状态码
    ]
    
    #现货状态,每个渠道必须字段
    MUST_DETAIL_ATTR = [
        'img',              #默认图片
        'name',             #名称
        'imgs',             #所有图片
        'price',            #现价
        'color',            #颜色名称
        'brand',            #品牌
        'descr',            #描述
        'status',           #状态
        'sizes',            #规格
        'colorId',          #颜色ID
        'backUrl',          #返回链接
        'listPrice',        #原价
        'productId',        #产品ID
        'currency',         #价格单位
        'status_code',      #HTTP状态码
        'currencySymbol',   #价格符号
    ]

    #现货状态,每个渠道可选字段
    ALL_DETAIL_ATTR = set(MUST_DETAIL_ATTR)
    ALL_DETAIL_ATTR.add('productCode')              #返回的商品编号／sku.
    ALL_DETAIL_ATTR.add('productSku')               #返回的商品编号／sku.
    ALL_DETAIL_ATTR.add('gender')                   #返回的商品性别
    ALL_DETAIL_ATTR.add('size_guide')               #返回的商品尺码指南
    ALL_DETAIL_ATTR.add('stock')                    #返回的商品总库存
    ALL_DETAIL_ATTR.add('manufacturer')             #返回的商品生产商
    ALL_DETAIL_ATTR.add('category')                 #返回的商品分类
    ALL_DETAIL_ATTR.add('subcategory')              #返回的商品子分类
    ALL_DETAIL_ATTR.add('season')                   #返回的商品季节
    ALL_DETAIL_ATTR.add('ip_port')                  #返回的ip和端口
    ALL_DETAIL_ATTR.add('returns')                  #退货信息
    ALL_DETAIL_ATTR.add('video')                    #视频信息,jdsports渠道
    ALL_DETAIL_ATTR.add('delivery')                 #配送信息
    ALL_DETAIL_ATTR.add('spinImgSet')               #旋转图片,jdsports渠道
    ALL_DETAIL_ATTR.add('brandDescr')               #品牌描述
    ALL_DETAIL_ATTR.add('note')                     #注意事项
    ALL_DETAIL_ATTR.add('rate')                     #税率,nysochina渠道
    ALL_DETAIL_ATTR.add('detail')                   #产品详细
    ALL_DETAIL_ATTR.add('designer')                 #设计详细
    ALL_DETAIL_ATTR.add('sizeFit')                  #尺码描述
    ALL_DETAIL_ATTR.add('model')                    #模特信息
    ALL_DETAIL_ATTR.add('fabric')                   #产品构造
    ALL_DETAIL_ATTR.add('seasonPremise')            #产品系列
    ALL_DETAIL_ATTR.add('presellDate')              #预售日期
    ALL_DETAIL_ATTR.add('everlaneApi')              #everlane的api链接
    ALL_DETAIL_ATTR.add('madeIn')                   #在哪儿制造.
    ALL_DETAIL_ATTR.add('amazon_need_wait')         #amazon需要延迟?
    ALL_DETAIL_ATTR.add('nysoInfoData')             #nyso调试
    ALL_DETAIL_ATTR.add('nysoStockData')            #nyso调试

    #部分渠道特有字段,不返回
    SPICAL_DETAIL_ATTR = [
        'keys'             #多颜色区分KEY
    ]

    #列表返回字段
    GET_MULTI_INFO = [
        'url',
        'img',
        'name',
        'price'
    ]

    ALL_MULTI_INFO = set(GET_MULTI_INFO)

    LOGGER = get_logger()

        

        
