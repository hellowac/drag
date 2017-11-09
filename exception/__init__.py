#coding:utf-8


#conf 中定义的MUST Key 不存在 error
class NotMustKeyError(Exception):
    pass

#conf 中定义的MUST Key 为空 error
class MustKeyEmptyError(Exception):
    pass

#conf 中定义的MUST Key 的 keys中 Key not found error
class NotMustSubKeyError(Exception):
    pass

