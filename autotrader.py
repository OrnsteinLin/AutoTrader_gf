# coding=utf-8
import easytrader
import threading
import time
from PyQt5 import QtCore, QtGui, QtWidgets

import mylog
import logging
from astrategy import AStrategy
from Ui_autotraderwin import Ui_AutoTraderWin
from mygftrader import Mygftrader


class AutoTrader(QtWidgets.QMainWindow, Ui_AutoTraderWin):

	def __init__(self, account_info, parent=None):
		"""构造函数
		param:
		account_info: 账户信息json文件地址
		"""
		super(AutoTrader, self).__init__(parent)
		self.setupUi(self)

		self.login_info = account_info
		#print(self.login_info)
		self.if_login = False
		
		self.if_running = False

		self.setupUi_plus()
		self.setupUi_signal_slot()

		easytrader.log.handlers.append(mylog.myfilech)
		

	def account_login(self):
		mylog.mylog.debug('Starting loginning')
		#self.myaccount = easytrader.use('gf')
		self.myaccount = Mygftrader()
		self.myaccount.prepare(self.login_info)
	
	def setupUi_plus(self):
		"""额外的Ui设置内容
		"""
		self.steptimer = QtCore.QTimer()



	def setupUi_signal_slot(self):
		"""信号和槽函数的链接
		"""
		self.steptimer.timeout.connect(self.on_steptimer)


	@QtCore.pyqtSlot()
	def on_steptimer(self):
		"""AutoTrader类功能的主要函数，每隔一段时间执行策略
		"""
		now = time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(time.time()))
		timepoint_0 = time.strftime('%Y-%m-%d',time.localtime(time.time()))+'-09:29:30'
		timepoint_1 = time.strftime('%Y-%m-%d',time.localtime(time.time()))+'-11:29:30'
		timepoint_2 = time.strftime('%Y-%m-%d',time.localtime(time.time()))+'-13:00:30'
		timepoint_3 = time.strftime('%Y-%m-%d',time.localtime(time.time()))+'-14:59:30'
		if now < timepoint_0 or (now > timepoint_1 and now < timepoint_2):
			mylog.mylog.debug('Out of time, pass')
			return
		elif now > timepoint_3:
			self.on_pushButton_stop_clicked()
			return

		easytrader.log.setLevel(logging.ERROR)
		astrategytemp = AStrategy(self.myaccount.balance, self.myaccount.position, self.myaccount.entrust)
		result = astrategytemp.get_strategy_gf()
		easytrader.log.setLevel(logging.DEBUG)
		self.deal_strategy_result(result)

			
	@QtCore.pyqtSlot()
	def on_pushButton_start_clicked(self):
		if not self.if_login:
			easytrader.log.setLevel(logging.WARNING)
			self.account_login()
			easytrader.log.setLevel(logging.DEBUG)
			self.if_login = True
		if not self.if_running:
			self.steptimer.start(18000)
			mylog.mylog.debug('Running started')
			self.if_running = True
			self.pushButton_start.setEnabled(False)
			self.pushButton_stop.setEnabled(True)


	@QtCore.pyqtSlot()
	def on_pushButton_stop_clicked(self):
		#self.test()
		if self.if_running:
			self.steptimer.stop()
			mylog.mylog.debug('Running stoped')
			self.if_running = False
			self.pushButton_start.setEnabled(True)
			self.pushButton_stop.setEnabled(False)

	@QtCore.pyqtSlot()
	def on_pushButton_test_clicked(self):
		self.test()

	def deal_strategy_result(self, s_result):
		"""这部分是雪球的
		for each in s_result:
			if each['todo'] == 'sell':
				self.myaccount.adjust_weight(each['id'], 0)
			elif each['todo'] == 'buy':
				self.myaccount.adjust_weight(each['id'], each['value_percent'])
		"""
		for each in s_result:
			if each['todo'] == 'sell':
				self.myaccount.sell(stock_code = each['id'], price = each['price'], amount = each['amount'])
			elif each['todo'] == 'buy':
				self.myaccount.buy(stock_code = each['id'], price = each['price'], volume = each['value'])
			elif each['todo'] == 'del':
				self.myaccount.cancel_entrust(entrust_no = each['entrust_id'])


	def test(self):
		#self.testastrategy = AStrategy()
		#print(self.testastrategy.A_filter)
		easytrader.log.setLevel(logging.WARNING)
		self.account_login()
		easytrader.log.setLevel(logging.DEBUG)
		tempbalance = self.myaccount.balance
		tempposition = self.myaccount.position
		tempentrust = self.myaccount.entrust
		tempposition['data'] = tempposition['data'][0:3]
		tempposition['data'][-1]['stock_code'] = '150012'
		self.testastrategy = AStrategy(tempbalance, tempposition, tempentrust)
		result = self.testastrategy.get_strategy_gf()
		#self.deal_strategy_result(result)
		
