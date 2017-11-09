#coding:utf-8

import time
from cfg import BaseCfg
# from utils import tool, freeProxyPool, usedProxyPool, updateProxyPool
from utils import tool
from exception import NotMustKeyError,NotMustSubKeyError
from requests.adapters import HTTPAdapter
try:
    import simplejson as json
except ImportError as e:
    import json
import requests


from requests.packages.urllib3.connectionpool import HTTPConnectionPool

#这招偷梁换柱好办法...
def _make_request(self,conn,method,url,**kwargs):

    response = self._old_make_request(conn,method,url,**kwargs)
    sock = getattr(conn,'sock',False)

    if sock:
        try:
            setattr(response,'peer',sock.getpeername())

        except AttributeError:
            
            #https的sock被封装过一层
            setattr(response,'peer',sock.socket.getpeername())
    else:
        setattr(response,'peer',None)

    return response

HTTPConnectionPool._old_make_request = HTTPConnectionPool._make_request
HTTPConnectionPool._make_request = _make_request


class DragBase(object):
    def __init__(self, cfg):
        super(DragBase, self).__init__()
        self.cfg = cfg
        # if not issubclass(cfg,BaseCfg) :
        if not isinstance(cfg,BaseCfg) :
            raise TypeError('{name} parent must extend BaseCfg'.format(name=cfg.CFG_NAME))


        self.session = requests.session()

        # 代理设置
        if cfg.USE['PROXY'] and cfg.USE['PROXY_TYPE'] == 'GENERAL' :
            self.session.proxies = cfg.PROXIES['GENERAL']

        elif cfg.USE['PROXY'] and cfg.USE['PROXY_TYPE'] == 'SOCKS' :
                # self.session = requesocks.session(config=dict(max_retries=cfg.MAX_RETRIES))
            self.session.proxies = cfg.PROXIES['SOCKS']

        self.session.mount('http://',HTTPAdapter(max_retries=cfg.MAX_RETRIES))
        self.session.mount('https://',HTTPAdapter(max_retries=cfg.MAX_RETRIES))


        self.session.max_redirects = 5  #最大重定向次数为5
        
        #日志记录器
        self.logger = cfg.LOGGER

        # 设置cookie ?
        if cfg.USE_COOKIES :
            self.session.cookies = cfg.COOKIEJAR

        #随机的弄一个头
        self.session.headers = tool.get_one_header()


    def update_cfg(self,cfg):
        self.__init__(cfg)



    def is_ok_status_code(self,status_code,pqhtml,url,resp):
        # 下架
        if status_code == 404:

            log_info = json.dumps(
                dict(time=time.time(), title=pqhtml('title').text(), url=url))

            self.logger.info(log_info)

            data = tool.get_off_shelf(
                                       code=status_code, 
                                       message=self.cfg.SOLD_OUT, 
                                       backUrl=resp.url, 
                                       html=pqhtml.outerHtml())

            return False,tool.return_data(successful=False, data=data)

        # 其他错误
        if status_code != 200:

            log_info = json.dumps(
                dict(time=time.time(), title=pqhtml('title').text(), url=url))

            self.logger.info(log_info)

            data = tool.get_error(
                                    code=status_code, 
                                    message=self.cfg.GET_ERR.get('SCERR', 'ERROR'), 
                                    backUrl=resp.url, 
                                    html=pqhtml.outerHtml())

            return False,tool.return_data(successful=False, data=data)

        return True,''

    def dispost(self,product):
        if product.has_key('keys') :
            return self.dispost_has_key(product)
        else :
            return self.dispost_no_key(product)

    #处理数据
    def dispost_no_key(self,product):

        attrs = self.cfg.ALL_DETAIL_ATTR
        must_attr = self.cfg.MUST_DETAIL_ATTR

        values = []

        obj = dict()
        for attr in attrs :
            try:
                obj[attr] = product[attr] if isinstance(product[attr],dict) else product[attr]

            except KeyError:
                if attr in must_attr :
                    raise NotMustKeyError('{cname} must Key "{key}" not found'.format(cname=self.cfg.CFG_NAME.lower(),key=attr))
                    
        values.append(obj)

        return values    

    #处理数据
    def dispost_has_key(self,product):
        
        keys = product['keys']

        attrs = self.cfg.ALL_DETAIL_ATTR
        must_attr = self.cfg.MUST_DETAIL_ATTR

        values = []

        for key in keys :
            obj = dict()
            for attr in attrs :
                try:
                    obj[attr] = product[attr][key] if isinstance(product[attr],dict) else product[attr]
                except KeyError as e:
                    if attr in must_attr :
                        self.logger.debug('NotMustKeyError : product -> :{0}'.format(product))
                        if e.message == attr :
                            raise NotMustKeyError('{cname} must Key "{key}" not found '.format(cname=self.cfg.CFG_NAME.lower(),key=attr))
                        else :
                            raise NotMustSubKeyError('{cname} subKeys "{key}" not found,parent key "{pKey}"'.format(pKey=attr,cname=self.cfg.CFG_NAME.lower(),key=e.message))
                
            values.append(obj)

        return values
        
        

