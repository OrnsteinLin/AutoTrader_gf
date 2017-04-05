# coding=utf-8
import requests
import time
import json
import os

import mylog

class AStrategy(object):

	def __init__(self, balance=None, position=None, entrust=None):
		"""构造函数
		param:
		in_balance: 当前资金情况（均为int或者float）
		[{'asset_balance': '资产总值',
   		'current_balance': '当前余额',
   		'enable_balance': '可用金额',
   		'market_value': '证券市值',
   		'money_type': '币种', #字符串
   		'pre_interest': '预计利息'}]

		in_position: 当前仓位情况（均为int或者float）
		[{'cost_price': '摊薄成本价', #字符串
   		'current_amount': '当前数量',
   		'enable_amount': '可卖数量',
   		'income_balance': '摊薄浮动盈亏',
   		'keep_cost_price': '保本价',
   		'last_price': '最新价',
   		'market_value': '证券市值',
   		'position_str': '定位串',
   		'stock_code': '证券代码',
   		'stock_name': '证券名称'}]

		in_entrust: 当前委托单情况
		[{'business_amount': '成交数量',
  		'business_price': '成交价格',
  		'entrust_amount': '委托数量',
  		'entrust_bs': '买卖方向', #字符串 买入 / 卖出
  		'entrust_no': '委托编号', #字符串
  		'entrust_price': '委托价格',
  		'entrust_status': '委托状态',  # 废单 / 已报？ /正常 /已撤？
  		'report_time': '申报时间', #'0'???
  		'stock_code': '证券代码',  #字符串
  		'stock_name': '证券名称'}] #字符串
		"""

		self.in_balance = balance
		self.in_position = position
		self.in_entrust = entrust

		self.A_filter_path = os.path.dirname(os.path.abspath(__file__)) + '/config/filter.json' 
		self.A_filter = self.read_json_file(self.A_filter_path) #A级筛选配置文件

		self.A_format_path = os.path.dirname(os.path.abspath(__file__)) + '/config/jisilu_data_format.json'
		self.A_format = self.read_json_file(self.A_format_path) #集思录数据格式

		self.gf_format_path = os.path.dirname(os.path.abspath(__file__)) + '/config/gf_data_format.json'
		self.gf_format = self.read_json_file(self.gf_format_path) #广发数据格式
	
		self.A_point_cal_path = os.path.dirname(os.path.abspath(__file__)) + '/config/point_cal.json'
		self.A_point_cal = self.read_json_file(self.A_point_cal_path) #分数计算加权
		#print(self.A_point_cal)

		self.A_s_config_path = os.path.dirname(os.path.abspath(__file__)) + '/config/strategy_config.json'
		self.A_s_config = self.read_json_file(self.A_s_config_path) #策略设置

		self.jisilu_data = self.get_jisilu_data() #获取集思录数据
		self.format_jisilu_data() #集思录数据格式修正
		#print(len(self.jisilu_data))	
		#print(self.jisilu_data['150012'])
		self.use_filter() #A级筛选
		#print(self.A_filter)
		#print(self.A_format)
		#print(len(self.jisilu_data))
		#print(self.jisilu_data['150012'])
		self.point_base = self.point_calculate_base() #计算分数所用的极大极小值
		#print(self.point_base)
		self.jisilu_data_point() #给jisilu数据中各个A级评分
		#tempdata = sorted(self.jisilu_data.items(), key= lambda x:x[1]['point'], reverse=True)
		#for eacht in tempdata:
		#	print(eacht[0] + '   ' +str(eacht[1]['point']))
		self.nowstatus = self.macket_status() #当前市场状态


		#从这里开始，与账户券商有关

		self.format_in_gf()
		
		#print(self.in_balance)
		#print(self.in_position)
		#print(self.in_entrust)
		

	def read_json_file(self, path):
		"""读取筛选文件，返回json
		"""
		with open(path, encoding = 'utf-8') as f:
			return json.load(f)

	def use_filter(self):
		"""使用筛选器进行筛选，筛选后的总表仍然存在jisilu_data中
		"""
		keys = list(self.jisilu_data.keys())
		for k in keys:
			#try:
			#	print(self.jisilu_data[k]['funda_lower_recalc_rt']+'\n')
			#except Exception as e:
			#	print(k)
			if k in self.A_filter['ban_A']:
				del self.jisilu_data[k]
				#print(k)
			elif (self.jisilu_data[k]['funda_amount']<self.A_filter['funda_amount_low'] or self.jisilu_data[k]['funda_lower_recalc_rt']<self.A_filter['funda_lower_recalc_rt_low']):
				del self.jisilu_data[k]
				#print(k)
			elif self.jisilu_data[k]['coupon_descr_s'] not in self.A_filter['coupon_descr_s_not']:
				del self.jisilu_data[k]



	def get_jisilu_data(self):
		"""获取集思录的实时数据json，返回处理过的数组
		原始数据格式：{'page':1, 'rows':[{'id':'zzzz','cell':{'xxx':'yyyy'}}]}
		处理后的数据格式：{'id0':{'xxx':'yyy'},'id1':{'xxx':'yyy'}....}
		funda_profit_rt_next: 修正收益率
		funda_discount_rt: 折价率（溢价则为负数）
		funda_amount: 份额（int）
		funda_current_price: 现价
		funda_value: 净值
		funda_lower_recalc_rt: 下折母基金需跌比例
		coupon_descr_s: +N利率
		"""
		url = "http://www.jisilu.cn/data/sfnew/funda_list/"
		url = url +'?___t='+str(int(time.time()*1000))
		rcontent = requests.get(url)
		rjson = rcontent.json()
		mylog.mylog.info('集思录数据 page:'+str(rjson['page'])+', rows:'+str(len(rjson['rows'])))
		rcontent.close()

		rdata = {}
		for each in rjson['rows']:
			rdata[each['id']] = each['cell']

		return rdata
		
	def format_jisilu_data(self):
		"""格式化集思录数据，异常输出为mylog.warning
		"""
		for eachA in self.jisilu_data:
			for item in self.jisilu_data[eachA]:
				try:
					if item in self.A_format['int']:
						self.jisilu_data[eachA][item] = int(self.jisilu_data[eachA][item])
					elif item in self.A_format['float']:
						self.jisilu_data[eachA][item] = float(self.jisilu_data[eachA][item])
					elif item in self.A_format['percent'] and item != 'fundb_upper_recalc_rt':
						self.jisilu_data[eachA][item] = float(self.jisilu_data[eachA][item].strip('%'))
					elif item in self.A_format['plus_percent']:
						#self.jisilu_data[eachA][item] = float(self.jisilu_data[eachA][item].strip('%+'))  #因为出现挺多这两个的特殊值
						pass
					elif item not in self.A_format['text'] and item != 'fundb_upper_recalc_rt':
						mylog.mylog.warning('格式转换出错jsl ' + eachA + ' ' + item + ' ' + self.jisilu_data[eachA][item])						
				except Exception as e:
					mylog.mylog.error(str(e) + '  ' + eachA + ' ' + item + ' ' + self.jisilu_data[eachA][item])
			

	def point_calculate_base(self):
		"""为了分数计算，需要初始化一个各项参数的极大极小值，返回内容为一个字典，其中各自有max和min和mid值：
		funda_profit_rt_next: 修正收益率
		funda_discount_rt: 折价率（溢价则为负数）
		funda_amount: 份额（int）
		funda_lower_recalc_rt: 下折母基金需跌比例
		"""
		templist_profit_rt_next = [self.jisilu_data[v]['funda_profit_rt_next'] for v in self.jisilu_data]
		templist_discount_rt = [self.jisilu_data[v]['funda_discount_rt'] for v in self.jisilu_data]
		templist_amount = [self.jisilu_data[v]['funda_amount'] for v in self.jisilu_data]
		templist_lower_recalc_rt = [self.jisilu_data[v]['funda_lower_recalc_rt'] for v in self.jisilu_data]
		#templist_profit_to_discount = [self.jisilu_data[v]['funda_profit_rt_next']/self.jisilu_data[v]['funda_discount_rt'] for v in self.jisilu_data]
		templist_profit_rt_next.sort()
		templist_discount_rt.sort()
		templist_amount.sort()
		templist_lower_recalc_rt.sort()
		#print(templist_lower_recalc_rt)
		point_base = {'funda_profit_rt_next_max' : templist_profit_rt_next[-1],
		'funda_profit_rt_next_mid' : templist_profit_rt_next[len(templist_profit_rt_next)//2],
		'funda_profit_rt_next_min' : templist_profit_rt_next[0],
		'funda_discount_rt_max' : templist_discount_rt[-1],
		'funda_discount_rt_mid' : templist_discount_rt[len(templist_discount_rt)//2],
		'funda_discount_rt_min' : templist_discount_rt[0],
		'funda_amount_max' : templist_amount[-1],
		'funda_amount_mid' : templist_amount[len(templist_amount)//2],
		'funda_amount_min' : templist_amount[0],
		'funda_lower_recalc_rt_max' : templist_lower_recalc_rt[-1],
		'funda_lower_recalc_rt_mid' : templist_lower_recalc_rt[len(templist_lower_recalc_rt)//2],
		'funda_lower_recalc_rt_min' : templist_lower_recalc_rt[0]
		}
		return point_base

	def point_calculate(self, f_profit_rt_next, f_discount_rt, f_amount, f_lower_recalc_rt):
		"""分数计算
		param:
		详情见函数get_jisulu_data
		使用了中位数
		"""
		temppoint = self.A_point_cal['funda_profit_rt_next'] * self.point_calculate_use_mid(f_profit_rt_next, self.point_base['funda_profit_rt_next_mid'], self.point_base['funda_profit_rt_next_min'])
		temppoint += self.A_point_cal['funda_discount_rt'] * self.point_calculate_use_mid(f_discount_rt, self.point_base['funda_discount_rt_mid'], self.point_base['funda_discount_rt_min'])
		temppoint += self.A_point_cal['funda_amount'] * self.point_calculate_use_mid(f_amount, self.point_base['funda_amount_mid'], self.point_base['funda_amount_min'])
		temppoint += self.A_point_cal['funda_lower_recalc_rt'] * self.point_calculate_use_mid(f_amount, self.point_base['funda_lower_recalc_rt_mid'], self.point_base['funda_lower_recalc_rt_min'])
		#if f_discount_rt > 0:
		#	temppoint += self.A_point_cal['profit_to_discount']
		#else:
		#	temppoint += self.A_point_cal['profit_to_discount'] * 
		return [f_profit_rt_next, temppoint]

	def point_calculate_use_mid(self, f_in, f_up, f_low):
		"""使用上下限算分数，因为是python3，所以使用/即可
		"""
		if f_in >= f_up:
			return 1.0
		else:
			return (f_in - f_low) / (f_up - f_low) 

	def jisilu_data_point(self):
		"""为筛选后的jisilu数据添加point
		"""
		for eachA in self.jisilu_data:
			self.jisilu_data[eachA]['point'] = self.point_calculate(self.jisilu_data[eachA]['funda_profit_rt_next'], self.jisilu_data[eachA]['funda_discount_rt'], self.jisilu_data[eachA]['funda_amount'], self.jisilu_data[eachA]['funda_lower_recalc_rt'])


	def format_in_gf(self):
		"""格式化广发的输入数据
		gf.balance
		{
			'data': 
			[
				{
					'rate_kind': '0', 
					'fine_integral': '0', 
					'opfund_market_value': '49001.00', 
					'begin_balance': '1000.14', 
					'frozen_balance': '0', 
					'fund_balance': '890.24', 
					'asset_balance': '49996.14', #总资产
					'interest': '0', 
					'unfrozen_balance': '0', 
					'foregift_balance': '0', 
					'entrust_buy_balance': '221.50', 
					'fetch_balance': '1000.14', 
					'enable_balance': '49779.64', #可用资产
					'money_type': '0', 
					'current_balance': '1000.14', 
					'fetch_cash': '1000.14', 
					'real_sell_balance': '0', 
					'real_buy_balance': '109.90', 
					'integral_balance': '2070.96', 
					'net_asset': '49996.14', 
					'market_value': '104.90', 
					'money_type_dict': '人民币', 
					'mortgage_balance': '0', 
					'pre_interest_tax': '0', 
					'fetch_balance_old': '0', 
					'pre_fine': '0', 
					'correct_balance': '0', 
					'pre_interest': '0.02'
				}
			], 
			'success': True, 
			'total': 1
		}

		gf.postition
		{
			'total': 1, 
			'success': True, 
			'data': 
			[
				{
					'hold_amount': '0', 
					'stock_type': 'L', 
					'income_balance': '-5.00', 
					'income_balance_nofare': '-5.00', 
					'fund_account': '9237965', 
					'exchange_type': '2', 
					'client_id': '184900125551', 
					'av_income_balance': '0', 
					'hand_flag': '0', 
					'uncome_sell_amount': '0', 
					'cost_balance': '109.90', 
					'stock_account': '0184731551', 
					'exchange_type_dict': '深圳', 
					'profit_ratio': '-4.55', 
					'frozen_amount': '0', 
					'entrust_sell_amount': '0', 
					'keep_cost_price': '1.099', 
					'stock_name': '一带一A', 
					'asset_price': '1.049', 
					'av_buy_price': '0', 
					'delist_flag': '0', 
					'cost_price': '1.099', 
					'uncome_buy_amount': '0', 
					'position_str': '01849000000000009237965000200000000000184731551150275', 
					'enable_amount': '0', 
					'par_value': '1.000', 
					'delist_date': '0', 
					'real_sell_amount': '0', 
					'current_amount': '100.00', 
					'market_value': '104.90', 
					'stock_code': '150275', 
					'real_buy_amount': '100.00', 
					'last_price': '1.0490'
				}
			], 
			'error_no': 0
		}

		gf.entrust
		{
			'total': 1, 
			'success': True, 
			'data': 
			[
				{
					'entrust_date': '20161123', 
					'stock_type': 'L', 
					'stock_account': '0184731551', 
					'fund_account': '9237965', 
					'exchange_type': '2', 
					'stock_name': '中证100A', 
					'meeting_seq': ' ', 
					'entrust_prop_dict': '买卖', 
					'entrust_no': '52686', 
					'cancel_info': ' ', 
					'business_amount': '0', 
					'order_id': '52686', 
					'op_station': 'WEB|IP:117.136.79.56,MAC:A0-D3-7A-90-17-67,172.20.10.2,HDD:W62CMRPN,ORIGIN:WEB;MOBILE', 
					'report_milltime': '151117605', 
					'batch_no': '52686', 
					'entrust_price': '1.066', 
					'entrust_time': '151117', 
					'report_time': '151117', 
					'entrust_bs_dict': '买入', 
					'curr_milltime': '151117600', 
					'entrust_amount': '100.00', 
					'report_no': '52686', 
					'entrust_prop': '0', 
					'entrust_type_dict': '委托', 
					'business_price': '0', 
					'orig_order_id': '52686', 
					'position_str': '20161123041511176000184900052686', 
					'business_balance': '0', 
					'init_date': '20161123', 
					'entrust_status': '2', 
					'entrust_way': '7', 
					'entrust_status_dict': '已报', 
					'entrust_bs': '1', 
					'withdraw_amount': '0', 
					'stock_code': '150012', 
					'entrust_type': '0'
				}
			]
		}

		"""
		self.in_balance = self.in_balance['data'][0]
		for each in self.in_balance:
			if each in self.gf_format['balance']['float']:
				self.in_balance[each] = float(self.in_balance[each])
			elif each not in self.gf_format['balance']['text']:
				mylog.mylog.warning('格式转换出错gf_balance ' + each + ' ' + self.in_balance[each])

		if self.in_position['total'] > 0:
			self.in_position = self.in_position['data']
			for eachA in self.in_position:
				for item in eachA:
					if item in self.gf_format['position']['float']:
						eachA[item] = float(eachA[item])
					elif item not in self.gf_format['position']['text']:
						mylog.mylog.warning('格式转换出错gf_position ' + item + eachA[item])
			self.in_position = [v for v in self.in_position if v['current_amount'] > 0]
		else:
			self.in_position = []
			mylog.mylog.warning('Position is empty')

		for eachA in self.in_position:
			if eachA['stock_code'] in self.jisilu_data:
				eachA['point'] = self.jisilu_data[eachA['stock_code']]['point']
			else:
				eachA['point'] = [0, 0]

		self.in_position = sorted(self.in_position, key = lambda x : x['point'][0], reverse =True)
		
		templist = ['已成', '废单', '已撤', '部撤']
		if self.in_entrust['total'] > 0:
			self.in_entrust = self.in_entrust['data']
			for eachA in self.in_entrust:
				for item  in eachA:
					if item in self.gf_format['entrust']['float']:
						eachA[item] = float(eachA[item])
					elif item not in self.gf_format['entrust']['text']:
						mylog.mylog.warning('格式转换出错gf_entrust ' + item + eachA[item])
			self.in_entrust = [v for v in self.in_entrust if v['entrust_status_dict'] not in templist]
			self.in_entrust_buy = [v for v in self.in_entrust if v['entrust_bs_dict'] == '买入']
			self.in_entrust_sell = [v for v in self.in_entrust if v['entrust_bs_dict'] == '卖出']
		else:
			self.in_entrust = []
			self.in_entrust_buy = []
			self.in_entrust_sell = []

	def get_strategy_gf(self):
		"""核心函数，获取返回的操作。
		"""
		tempjisilu_data = {v:self.jisilu_data[v] for v in self.jisilu_data if self.jisilu_data[v]['point'][1] >= self.A_s_config['min_point']} #清洗分数过低的A
		tempdatalist = sorted(tempjisilu_data.items(), key= lambda x:x[1]['point'][0], reverse=True)
		tempdata = [v[0] for v in tempdatalist]
		tempdata = tempdata[0:self.A_s_config['max_A']+1]

		mylog.mylog.info('TOP3:  '+str(tempdata))
		mylog.mylog.info('NowPosition:  '+ str([v['stock_code'] for v in self.in_position]))

		strategy_result = self.get_strategy_del_gf(tempdata) 
		if len(self.in_position) > self.A_s_config['max_A']:
			strategy_result += self.get_strategy_sell_gf(tempdata)
		elif len(self.in_position) < self.A_s_config['max_A']:
			strategy_result += self.get_strategy_sell_gf(tempdata)
			strategy_result += self.get_strategy_buy_gf(tempdata)
		elif not set(tempdata).issubset(set([v['stock_code'] for v in self.in_position])) :
			strategy_result += self.get_strategy_sell_gf(tempdata)
			strategy_result += self.get_strategy_buy_gf(tempdata)
		else:
			strategy_result = []
		if strategy_result == []:
			strategy_result += self.get_strategy_buyold(tempdata)
		return strategy_result

	def get_strategy_sell_gf(self, in_data):
		self.in_position.reverse()
		tempresult = []
		for eachA in self.in_position:
			if eachA['stock_code'] not in self.jisilu_data:
				continue
			if eachA['stock_code'] not in in_data[0:self.A_s_config['max_A']] and eachA['enable_amount'] > 0 and self.jisilu_data[in_data[self.A_s_config['max_A']-1]]['point'][0] - eachA['point'][0] >= self.A_s_config['min_dis']:
				tempresult += [{'todo' : 'sell', 'id' : eachA['stock_code'], 'amount' : eachA['enable_amount'], 'price' : eachA['last_price']},]
				if self.nowstatus > self.A_s_config['status_dis'] and self.jisilu_data[eachA['stock_code']]['funda_increase_rt'] > 0 and self.jisilu_data[eachA['stock_code']]['funda_increase_rt'] < 0.5 * self.A_s_config['status_dis']:
					tempresult[-1]['price'] += 0.001
				mylog.mylog.info('sell: id: '+ tempresult[-1]['id'] +' amount: '+str(tempresult[-1]['amount'])+' price: '+str(tempresult[-1]['price']) + ' nowprice: ' + str(eachA['last_price']))
		return tempresult

	def get_strategy_buy_gf(self, in_data):
		if len(self.in_position) + len(self.in_entrust_buy) > self.A_s_config['max_A'] + 1:
			print('e1')
			return []
		"""持仓不可为空
		"""

		if self.in_balance['asset_balance'] - self.in_balance['enable_balance']  > self.A_s_config['max_position'] * self.in_balance['asset_balance']:
			return []

		if len(self.in_position) > 0:
			tempposition = [v['stock_code'] for v in self.in_position]
		else:
			tempposition = []

		if len(self.in_entrust_buy) >0:
			tempentrustbuy = [v['stock_code'] for v in self.in_entrust_buy]
		else:
			tempentrustbuy = []

		tempresult = []
		for eachA in in_data :
			if eachA not in tempposition and eachA not in tempentrustbuy:
				tempbuyvalue = self.A_s_config['each_position'] * self.in_balance['enable_balance']
				if tempbuyvalue < self.A_s_config['min_position_value'] :
					if self.in_balance['enable_balance'] > self.A_s_config['min_position_value'] :
						tempbuyvalue = self.A_s_config['min_position_value']
					else:
						tempbuyvalue = self.in_balance['enable_balance']-5.0
				tempresult = [{'todo': 'buy', 'id' : eachA, 'value': tempbuyvalue, 'price': self.jisilu_data[eachA]['funda_current_price']},]
				if self.nowstatus < -self.A_s_config['status_dis'] and self.jisilu_data[eachA]['funda_increase_rt'] < 0 and self.jisilu_data[eachA]['funda_increase_rt'] > 0.5 * -self.A_s_config['status_dis']:
					tempresult[0]['price'] += -0.001
				mylog.mylog.info('buy: '+ tempresult[0]['id'] +'  value:  '+ str(tempresult[0]['value']) + ' price: '+str(tempresult[0]['price']) + ' nowprice: ' + str(self.jisilu_data[eachA]['funda_current_price']))
				break
		return tempresult

	def get_strategy_del_gf(self, in_data):
		"""撤单内容
		"""
		tempresult = []
		if len(self.in_entrust_buy) > 0:
			for eachA in self.in_entrust_buy:
				if eachA['stock_code'] not in self.jisilu_data:
					continue
				if self.jisilu_data[eachA['stock_code']]['funda_current_price'] - eachA['entrust_price'] > self.A_s_config['max_price_dis'] or (eachA['stock_code'] not in in_data and self.jisilu_data[in_data[self.A_s_config['max_A']-1]]['point'][0] - self.jisilu_data[eachA['stock_code']]['point'][0] > self.A_s_config['min_dis']):
					tempresult +=  [{'todo' : 'del', 'entrust_id' : eachA['entrust_no']}]
					mylog.mylog.info('del: '+eachA['stock_code'] + '  entrust_id: '+eachA['entrust_no'])
		if len(self.in_entrust_sell) > 0:
			for eachA in self.in_entrust_sell:
				if eachA['stock_code'] not in self.jisilu_data :
					continue
				if eachA['stock_code'] in in_data[0:self.A_s_config['max_A']] or eachA['entrust_price'] - self.jisilu_data[eachA['stock_code']]['funda_current_price'] > self.A_s_config['max_price_dis']:
					tempresult +=  [{'todo' : 'del', 'entrust_id' : eachA['entrust_no']}]
					mylog.mylog.info('del: '+eachA['stock_code'] + '  entrust_id: ' + eachA['entrust_no'])
		return tempresult

	def get_strategy_buyold(self, in_data):
		"""补仓
		"""
		if self.in_balance['asset_balance'] - self.in_balance['enable_balance']  > self.A_s_config['max_position'] * self.in_balance['asset_balance']:
			return []
		tempresult = []

		if len(self.in_entrust_buy) >0:
			tempentrustbuy = [v['stock_code'] for v in self.in_entrust_buy]
		else:
			tempentrustbuy = []
		for each in self.in_position:
			if each['stock_code'] in in_data and each['stock_code'] not in tempentrustbuy and each['cost_balance'] < self.A_s_config['min_position_value']*0.7:
				tempbuyvalue = self.A_s_config['min_position_value']-each['cost_balance']
				if tempbuyvalue > self.in_balance['enable_balance']:
					tempbuyvalue = self.in_balance['enable_balance'] - 5.0 - each['cost_balance']
				tempresult = [{'todo': 'buy', 'id' : each['stock_code'], 'value': tempbuyvalue, 'price': self.jisilu_data[each['stock_code']]['funda_current_price']},]
				mylog.mylog.info('buyold: '+ tempresult[0]['id'] +'  value:  '+ str(tempresult[0]['value']) + ' price: '+str(tempresult[0]['price']) + ' nowprice: ' + str(self.jisilu_data[each['stock_code']]['funda_current_price']))
				return tempresult
		return tempresult
		



	def macket_status(self):
		"""市场状态
		采用算完分数，但未使用分数筛选的jisilu data计算。
		"""
		tempresult = 0
		for eachA in self.jisilu_data:
			tempresult += self.jisilu_data[eachA]['funda_increase_rt']
		tempresult = tempresult/len(self.jisilu_data)
		mylog.mylog.info('Now macket status: ' + str(tempresult))
		return tempresult
