# coding:utf8
import logging
import os
import time

mylog = logging.getLogger('AutoTrader')
mylog.setLevel(logging.DEBUG)
mylog.propagate = False

myfmt = logging.Formatter('%(asctime)s [%(levelname)s] %(filename)s %(lineno)s: %(message)s')
mych = logging.StreamHandler()

logfilepath = os.path.dirname(__file__) + '/log/LOG'+time.strftime('%Y%m%d',time.localtime(time.time()))+'.txt'

myfilech = logging.FileHandler(logfilepath)
#print(logfilepath)
#print(os.path.dirname(__file__))

mych.setFormatter(myfmt)
myfilech.setFormatter(myfmt)#这是输出到日志文件的流

mylog.handlers.append(mych)
mylog.handlers.append(myfilech)
