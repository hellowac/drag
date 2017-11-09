# coding:utf-8

from cfg import BaseCfg,InstanceCfg
from exception import MustKeyEmptyError

try:
    # Python 3
    from urllib.parse import urlparse, parse_qs
except ImportError:
    # Python 2
    from urlparse import urlparse, parse_qs


class DragTools:

    @staticmethod
    def get_domain(url):
        if not isinstance(url, basestring):
            raise TypeError('get_domain parames Type Error ,must type str,but "{type}"'.format(type=type(url)))

        url_ = url.split('/')
        domain = url_[0]+'//'+url_[2]

        return domain


    @staticmethod
    def get_protocol(url_):
        if not isinstance(url_, basestring):
            raise TypeError('get_protocol parames Type Error ,must type str,but "{type}"'.format(type=type(url_)))

        return url_.split(':')[0]


    @staticmethod
    def get_domain_name(url):
        if not isinstance(url, basestring):
            raise TypeError('get_domain_name parames Type Error ,must type str,but "{type}"'.format(type=type(url)))

        url_ = url.split('/')
        url_ = url_[2].split('.')
        if len(url_) > 2:
            name = url_[1]
        elif len(url_) == 2:
            name = url_[0]
        else:
            raise ValueError, 'get_domain_name By Url Fail'

        # 配置 比如 6pm 的名称
        return BaseCfg.SPICAL_CHANNEL_NAMES.get(name, name)


    @staticmethod
    def get_one_header():

        header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            # 'Accept-Language': random.choice(BaseCfg.REQUEST_ACCEPT_LANGUAGE),
            # 'User-Agent': random.choice(BaseCfg.REQUEST_USER_AGENTS),
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Connection':'Keep-Alive',
            'Cache-Control':'max-age=0',
            'Upgrade-Insecure-Requests':'1',
            # Referer: http://www.gilt.com/sale/women
        }

        return header


    @staticmethod
    def get_unit(currency):
        return {
            'USD': u'$',           #美国
            'EUR': u'€',           #欧洲货币联盟
            'CNY': u'￥',          #中国
            'JPY': u'¥',           #日本 
            'GBP': u'£',           #英国 
            'CAD': u'C$',          #加拿大
            'BRL': u'R$',          #巴西
            'TWD': u'TWD',         #台湾币
            'HKD': u'HK$',         #中国香港
            'MOP': u'MOP',         #中国澳门
            'KPW': u'KPW',         #朝鲜 
            'VND': u'VND',         #越南 
            'LAK': u'LAK',         #老挝 
            'KHR': u'KHR',         #柬埔寨 
            'PHP': u'PHP',         #菲律宾 
            'MYR': u'MYR',         #马来西亚 
            'SGD': u'SGD',         #新加坡 
            'THP': u'THP',         #泰国 
            'BUK': u'BUK',         #缅甸
            'LKR': u'LKR',         #斯里兰卡 
            'MVR': u'MVR',         #马尔代夫 
            'IDR': u'IDR',         #印度尼西亚 
            'PRK': u'PRK',         #巴基斯坦
            'INR': u'INR',         #印度
            'NPR': u'NPR',         #尼泊尔 
            'AFA': u'AFA',         #阿富汗
            'IRR': u'IRR',         #伊朗 
            'IQD': u'IQD',         #伊拉克
            'SYP': u'SYP',         #叙利亚 
            'LBP': u'LBP',         #黎巴嫩
            'JOD': u'JOD',         #约旦
            'SAR': u'SAR',         #沙特阿拉伯
            'KWD': u'KWD',         #科威特
            'BHD': u'BHD',         #巴林 
            'QAR': u'QAR',         #卡塔尔
            'OMR': u'OMR',         #阿曼
            'YER': u'YER',         #阿拉伯也门
            'YDD': u'YDD',         #民主也门
            'TRL': u'TRL',         #土耳其
            'CYP': u'CYP',         #塞浦路斯
            'ISK': u'ISK',         #冰岛 
            'DKK': u'DKK',         #丹麦 
            'NOK': u'NOK',         #挪威 
            'SEK': u'SEK',         #瑞典 
            'FIM': u'FIM',         #芬兰 
            'SUR': u'SUR',         #俄罗斯 
            'PLZ': u'PLZ',         #波兰 
            'CSK': u'CSK',         #捷克和斯洛伐克
            'HUF': u'HUF',         #匈牙利 
            'DEM': u'DEM',         #德国 
            'ATS': u'ATS',         #奥地利 
            'CHF': u'CHF',         #瑞士 
            'NLG': u'NLG',         #荷兰 
            'BEF': u'BEF',         #比利时
            'LUF': u'LUF',         #卢森堡 
            'IEP': u'IEP',         #爱尔兰 
            'FRF': u'FRF',         #法国 
            'ESP': u'ESP',         #西班牙 
            'PTE': u'PTE',         #葡萄牙
            'ITL': u'ITL',         #意大利 
            'MTP': u'MTP',         #马耳他 
            'YUD': u'YUD',         #南斯拉夫 
            'ROL': u'ROL',         #罗马尼亚 
            'BGL': u'BGL',         #保加利亚 
            'ALL': u'ALL',         #阿尔巴尼亚 
            'GRD': u'GRD',         #希腊 
            'MXP': u'MXP',         #墨西哥 
            'GTQ': u'GTQ',         #危地马拉 
            'SVC': u'SVC',         #萨尔瓦多 
            'HNL': u'HNL',         #洪都拉斯 
            'NIC': u'NIC',         #尼加拉瓜 
            'CRC': u'CRC',         #哥斯达黎加 
            'PAB': u'PAB',         #巴拿马
            'CUP': u'CUP',         #古巴
            'BSD': u'BSD',         #巴哈马联邦 
            'JMD': u'JMD',         #牙买加 
            'HTG': u'HTG',         #海地 
            'DOP': u'DOP',         #多米尼加 
            'TTD': u'TTD',         #特立尼达和多巴哥 
            'BBD': u'BBD',         #巴巴多斯 
            'COP': u'COP',         #哥伦比亚 
            'VEB': u'VEB',         #委内瑞拉 
            'GYD': u'GYD',         #圭亚那
            'SRG': u'SRG',         #苏里南 
            'PES': u'PES',         #秘鲁 
            'ECS': u'ECS',         #厄瓜多尔 
            'BRC': u'BRC',         #巴西
            'BOP': u'BOP',         #玻利维亚 
            'CLP': u'CLP',         #智利 
            'ARP': u'ARP',         #阿根廷 
            'PYG': u'PYG',         #巴拉圭 
            'UYP': u'UYP',         #乌拉圭 
            'EGP': u'EGP',         #埃及 
            'LYD': u'LYD',         #利比亚 
            'SDP': u'SDP',         #苏丹
            'TND': u'TND',         #突尼斯
            'DZD': u'DZD',         #阿尔及利亚
            'MAD': u'MAD',         #摩洛哥
            'MRO': u'MRO',         #毛里塔尼亚 
            'XOF': u'XOF',         #塞内加尔,尼泊尔,上沃尔特,科特迪瓦,多哥,贝宁
            'GMD': u'GMD',         #冈比亚 
            'GWP': u'GWP',         #几内亚比绍 
            'GNS': u'GNS',         #几内亚 
            'SLL': u'SLL',         #塞拉里昂
            'LRD': u'LRD',         #利比里亚 
            'GHC': u'GHC',         #加纳
            'NGN': u'NGN',         #尼日利亚
            'XAF': u'XAF',         #喀麦隆,乍得,刚果,加蓬,中非
            'GQE': u'GQE',         #赤道几内亚 
            'ZAR': u'ZAR',         #南非 
            'DJF': u'DJF',         #吉布提
            'SOS': u'SOS',         #索马里 
            'KES': u'KES',         #肯尼亚 
            'UGS': u'UGS',         #乌干达 
            'TZS': u'TZS',         #坦桑尼亚 
            'RWF': u'RWF',         #卢旺达 
            'BIF': u'BIF',         #布隆迪 
            'ZRZ': u'ZRZ',         #扎伊尔 
            'ZMK': u'ZMK',         #赞比亚 
            'MCF': u'MCF',         #马达加斯加 
            'SCR': u'SCR',         #塞舌尔 
            'MUR': u'MUR',         #毛里求斯 
            'ZWD': u'ZWD',         #津巴布韦 
            'KMF': u'KMF',         #科摩罗 
            'AUD': u'AUD',         #澳大利亚 
            'NZD': u'NZD',         #新西兰 
            'FJD': u'FJD',         #斐济 
            'SBD': u'SBD',         #所罗门群岛 
        }[currency]


    @staticmethod
    def get_error(code=0, message=None, backUrl=None,html=None):

        return dict(status_code=code,status=BaseCfg.STATUS_ERROR,backUrl=backUrl, message=message,html=html)


    @staticmethod
    def return_data(successful=False, data=None):

        return dict(successful=successful,data=data)


    @staticmethod
    def get_off_shelf(code=0, message=None, backUrl=None,html=None):

        return dict(status_code=code,status=BaseCfg.STATUS_OFFSHELF,backUrl=backUrl, message=message,html=html)


    @staticmethod
    def get_down_img(name, url, session):
        try:
            fileName = name +url[url.rindex('/')+1:]

            if '?' in fileName : fileName = fileName.split('?')[0]

            filePath = os.path.join(BaseCfg.STORE_IMG_PATH,fileName)

            fileURL = BaseCfg.REQUEST_IMG_PATH+fileName

            if os.path.exists(filePath) :
                return fileURL

            r = session.get(url)
            if r.status_code == 200:
                with open(filePath, 'wb') as fw:
                    for chunk in r.iter_content(1024):
                        fw.write(chunk)

            return fileURL
        except Exception as e:
            e.message += ('Down img Fail,url :'+url)
            raise e


    @staticmethod
    def get_down_one_img(name, url, session):

        if not isinstance(url, basestring):
            raise TypeError, 'get_down_one_img parames Type Error ,must type str,but "{type}"'.format(type=type(url))

        return get_down_img(name,url,session)


    @staticmethod
    def get_down_all_img(name, urls, session):

        if not isinstance(url, list):
            raise TypeError, 'get_down_one_img parames Type Error ,must type list,but "{type}"'.format(type=type(url))

        # paths = []
        paths = [ get_down_img(name,url,session) for url in urls ]
            # paths.append(get_down_img(name,url,session))

        return paths

    @staticmethod
    def check_drag_detail(drag_res):
        keys = InstanceCfg.MUST_DETAIL_ATTR
        for res in drag_res :
            for key in keys :
                if not res[key] :
                    raise MustKeyEmptyError('key {0}\'s data is empty'.format(key))
        


def get_url_addr_and_params(url):
    o = urlparse(url)
    params = parse_qs(o.query)
    addr = o._replace(query=None).geturl()

    return url,params