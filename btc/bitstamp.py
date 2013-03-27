import urllib, urllib2, json
from decimal import Decimal

class BitStamp:
	def __init__(self, user=None, password=None):
		self.user = user
		self.password = password

	def generic_get(self, what, **kwargs):
		"""
		Do a GET request to https://www.bitstamp.net/api/<what>/ and
		return decoded json response data.

		If keyword arguments are specified they are urlencoded and passed as
		GET parameters.
		"""
		args = urllib.urlencode(kwargs)
		if args:
			args = '?' + args
		return json.load(urllib2.urlopen('https://www.bitstamp.net/api/%s/%s' % (what, args)))

	def generic_post(self, what, **kwargs):
		"""
		Do a POST request to https://www.bitstamp.net/api/<what>/ and
		return decoded json response data.

		If keyword arguments are specified they are urlencoded and passed as
		POST parameters.
		"""
		args = urllib.urlencode(kwargs)
		return json.load(urllib2.urlopen('https://www.bitstamp.net/api/%s/' % what, args))

	def ticker(self):
		"""
		Ticker

		GET https://www.bitstamp.net/api/ticker/

		Returns JSON dictionary:

			last - last BTC price
			high - last 24 hours price high
			low - last 24 hours price low
			volume - last 24 hours volume
			bid - highest buy order
			ask - lowest sell order
		"""
		return self.generic_get('ticker')

	def order_book(self, group=1):
		"""
		Order book

		GET https://www.bitstamp.net/api/order_book/

		Params:

			group - group orders with the same price (0 - false; 1 - true). Default: 1.

		Returns JSON dictionary with "bids" and "asks". Each is a list of open orders and
		each order is represented as a list of price and amount.

		"""
		return self.generic_get('order_book', group=group)

	def transactions(self, timedelta=3600):
		"""
		GET https://www.bitstamp.net/api/transactions/

		Params:

			timedelta - return transactions for the last 'timedelta' seconds. Default: 86400 seconds.
			Example: https://www.bitstamp.net/api/transactions/?timedelta=3600 will return transactions for the last hour (3600 seconds).

		Returns descending JSON list of transactions. Every transaction (dictionary) contains:

			date - unix timestamp date and time
			tid - transaction id
			price - BTC price
			amount - BTC amount
		"""
		return self.generic_get('transactions', timedelta=timedelta)

	def bitinstant(self):
		"""
		Bitinstant reserves

		GET https://www.bitstamp.net/api/bitinstant/

		Returns JSON dictionary:

		    usd - Bitinstant USD reserves
		"""
		return self.generic_get('bitinstant')

	def eur_usd(self):
		"""
		EUR/USD conversion rate

		GET https://www.bitstamp.net/api/eur_usd/

		Returns JSON dictionary:

			buy - buy conversion rate
			sell - sell conversion rate
		"""
		return self.generic_get('eur_usd')

	def balance(self):
		"""
		Account balance

		POST https://www.bitstamp.net/api/balance/

		Params:

			user - customer ID
			password - password

		Returns JSON dictionary:

			usd_balance - USD balance
			btc_balance - BTC balance
			usd_reserved - USD reserved in open orders
			btc_reserved - BTC reserved in open orders
			usd_available- USD available for trading
			btc_available - BTC available for trading
			fee - customer trading fee
		"""
		return self.generic_post('balance', user=self.user, password=self.password)

	def user_transactions(self, timedelta=3600):
		"""
		User transactions

		GET https://www.bitstamp.net/api/user_transactions/

		Params:

			user - customer ID
			password - password
			timedelta - return transactions for the last 'timedelta' seconds. Default: 86400 seconds.
			Example: https://www.bitstamp.net/api/transactions/?timedelta=3600 will return transactions for the last hour (3600 seconds).

		Returns descending JSON list of transactions. Every transaction (dictionary) contains:

			datetime - date and time
			id - transaction id
			type - transaction type (0 - deposit; 1 - withdrawal; 2 - market trade)
			usd - USD amount
			btc - BTC amount
			fee - transaction fee
		"""
		return self.generic_post('user_transactions', user=self.user, password=self.password, timedelta=timedelta)

	def open_orders(self):
		"""
		Open orders

		POST https://www.bitstamp.net/api/open_orders/

		Params:

			user - customer ID
			password - password

		Returns JSON list of open orders. Each order is represented as dictionary:

			id - order id
			datetime - date and time
			type - buy or sell (0 - buy; 1 - sell)
			price - price
			amount - amount
		"""
		return self.generic_post('open_orders', user=self.user, password=self.password)

	def cancel_order(self, id):
		"""
		Cancel order

		POST https://www.bitstamp.net/api/cancel_order/

		Params:

			user - customer ID
			password - password
			id - order ID

		Returns 'true' if order has been found and canceled.
		"""
		return self.generic_post('cancel_order', user=self.user, password=self.password, id=id)

	def buy(self, amount, price):
		"""
		Buy limit order

		POST https://www.bitstamp.net/api/buy/

		Params:

			user - customer ID
			password - password
			amount - amount
			price - price

		Returns JSON dictionary representing order:

			id - order id
			datetime - date and time
			type - buy or sell (0 - buy; 1 - sell)
			price - price
			amount - amount
		"""
		amount = str(Decimal(amount).quantize(Decimal('0.00000001')))[:17]
		price = str(Decimal(price).quantize(Decimal('0.01')))
		return self.generic_post('buy', user=self.user, password=self.password, amount=amount, price=price)

	def sell(self, amount, price):
		"""
		Sell limit order

		POST https://www.bitstamp.net/api/sell/

		Params:

			user - customer ID
			password - password
			amount - amount
			price - price

		Returns JSON dictionary representing order:

			id - order id
			datetime - date and time
			type - buy or sell (0 - buy; 1 - sell)
			price - price
			amount - amount
		"""
		amount = str(Decimal(amount).quantize(Decimal('0.00000001')))[:17]
		price = str(Decimal(price).quantize(Decimal('0.01')))
		return self.generic_post('sell', user=self.user, password=self.password, amount=amount, price=price)

	def create_code(self, usd=0, btc=0):
		"""
		Create Bitstamp code

		POST https://www.bitstamp.net/api/create_code/

		Params:

			user - customer ID
			password - password
			usd - USD amount (optional)
			btc - BTC amount (optional)

		Returns Bitstamp code string
		"""
		usd = str(Decimal(usd).quantize(Decimal('0.01')))
		btc = str(Decimal(btc).quantize(Decimal('0.00000001')))[:17]
		return self.generic_post('create_code', user=self.user, password=self.password, usd=usd, btc=btc)

	def check_code(self, code):
		"""
		Check Bitstamp code

		POST https://www.bitstamp.net/api/check_code/

		Params:

			user - customer ID
			password - password
			code - Bitstamp code to check

		Returns JSON dictionary containing USD and BTC amount included in given bitstamp code.
		"""
		return self.generic_post('check_code', user=self.user, password=self.password, code=code)

	def redeem_code(self, code):
		"""
		Redeem Bitstamp code

		POST https://www.bitstamp.net/api/redeem_code/

		Params:

			user - customer ID
			password - password
			code - Bitstamp code to redeem

		Returns JSON dictionary containing USD and BTC amount added to user's account.
		"""
		return self.generic_post('redeem_code', user=self.user, password=self.password, code=code)

	def sendtouser(self, customer_id, currency, amount):
		"""
		Send to user

		POST https://www.bitstamp.net/api/sendtouser/

		Params:

			user - customer ID
			password - password
			customer_id - Customer ID you wish to send funds to
			currency - Currency you wish to send: USD or BTC
			amount - Amount you wish to send

		Returns true if successful.
		"""
		if currency == 'BTC':
			amount = str(Decimal(amount).quantize(Decimal('0.00000001')))[:17]
		elif currency == 'USD':
			amount = Decimal(amount).quantize(Decimal('0.01'))
		return self.generic_post('create_code', user=self.user, password=self.password, customer_id=customer_id, currency=currency, amount=amount)

	def withdrawal_requests(self):
		"""
		Withdrawal requests

		POST https://www.bitstamp.net/api/withdrawal_requests/

		Params:

			user - customer ID
			password - password

		Returns JSON list of withdrawal requests. Each request is represented as dictionary:

			id - order id
			datetime - date and time
			type - (0 - SEPA; 1 - bitcoin; 2 - WIRE transfer; 3 and 4 - bitstamp code; 5 - Mt.Gox code)
			amount - amount
			status - (0 - open; 1 - in process; 2 - finished; 3 - canceled; 4 - failed)
			data - additional withdrawal request data (Mt.Gox code, etc.)
		"""
		return self.generic_post('withdrawal_requests', user=self.user, password=self.password)

	def bitcoin_withdrawal(self, amount, address):
		"""
		Bitcoin withdrawal

		POST https://www.bitstamp.net/api/bitcoin_withdrawal/

		Params:

			user - customer ID
			password - password
			amount - bitcoin amount
			address - bitcoin address

		Returns true if successful.
		"""
		amount = str(Decimal(amount))[:17]
		return self.generic_post('bitcoin_withdrawal', user=self.user, password=self.password, amount=amount, address=address)

	def bitcoin_deposit_address(self):
		"""
		Bitcoin deposit address

		POST https://www.bitstamp.net/api/bitcoin_deposit_address/

		Params:

			user - customer ID
			password - password

		Returns your bitcoin deposit address.
		"""
		return self.generic_post('bitcoin_deposit_address', user=self.user, password=self.password)


if __name__ == '__main__':
	b = BitStamp()
	print json.dumps(b.ticker(), indent=4)

