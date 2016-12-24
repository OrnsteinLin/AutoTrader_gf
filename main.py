# coding=utf-8
import logging
import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

import mylog
import autotrader
import mygftrader

def begin(debug=True, account_info = os.path.dirname(os.path.abspath(__file__)) + '/config/login.json'):
	"""从这里开始调用本工具，返回AutoTrader对象
	param:
	debug: 决定是否开启日志输出mylog，默认为True
	account_info: 账户信息json文件的地址，默认为当前程序目录下/config/login.json
	"""
	if not debug:
		mylog.mylog.handler = [logging.NullHandler()]
		#pass
	#print(account_info)
	#print(os.path.dirname(os.path.abspath(__file__)))
	#mylog.mylog.info('tttt_info')
	return autotrader.AutoTrader(account_info=account_info)

def test(self):
	return mygftrader.Mygftrader()



if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	#f_std = os.open(os.path.dirname(os.path.abspath(__file__)) + '/log/test.txt', os.O_RDWR|os.O_CREAT)
	#f_std = open(os.path.dirname(os.path.abspath(__file__)) + '/log/test.txt', 'w')
	#sys.stdout = f_std
	#sys.stderr = f_std
	user = begin()
	user.show()
	#user.test()
	sys.exit(app.exec_())
	#不会被执行。。print('exit')
