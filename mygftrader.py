# coding=utf-8
import easytrader.gftrader as gftrader
import six
import urllib

class Mygftrader(gftrader.GFTrader):
	"""easytrader中广发交易类的派生类，主要是修正其中部分函数的问题
	"""
	def __init__(self):
		super(Mygftrader, self).__init__()

		
	def __go_login_page(self):
		"""访问登录页面获取 cookie，重写"""
		if self.s is not None:
			self.s.get(self.config['logout_api'])

		self.s = requests.session()
		headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
		print('re')
		self.s.headers.update(headers)
		self.s.get(self.config['login_page'])

	def send_heartbeat(self):
		pass

"""
	def request(self, params):
		if six.PY2:
			params_str = urllib.urlencode(params)
			unquote_str = urllib.unquote(params_str)
		else:
			params_str = urllib.parse.urlencode(params)
			unquote_str = urllib.parse.unquote(params_str)
			url = self.trade_prefix + '?' + unquote_str
			r = self.s.post(url)
			log.debug('raw response: {}'.format(r.text))
		return r.content
"""