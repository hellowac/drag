#coding:utf-8
from ._dragbase import DragBase
from utils import tool

Instances = dict()
Instances_count = dict()

alias = dict(weinihaigou='nysochina')

#构建每个抓取实例
def Draws(cahnnelName,refresh=False):
    
    global Instances
    global Instances_count

    cahnnelName = alias.get(cahnnelName, cahnnelName)

    if cahnnelName in Instances and not refresh and Instances_count.get(cahnnelName,0) < 50:
        Instances_count[cahnnelName]+= 1
        return Instances[cahnnelName]

    cfgMoudle = __import__('cfg.{cName}Cfg'.format(cName=cahnnelName),(),(),['Cfg'],-1)
    coreMoudle = __import__('core.{cName}'.format(cName=cahnnelName),(),(),['Drag'],-1)

    icfg = cfgMoudle.Cfg
    iobj = coreMoudle.Drag

    ins = iobj(icfg())

    #保存到实例字典,方便以后调用.
    Instances[cahnnelName] = ins
    Instances_count[cahnnelName] = 0

    return ins

__all__ = [DragBase, tool, Draws]