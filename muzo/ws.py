from SOAPpy import WSDL
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from os.path import dirname
from signature import CSignature

MUZO_ORDER_STATES = {
    0: _('UNKNOWN'),
	1: _('REQUESTED'),
	2: _('PENDING'),
	3: _('CREATED'),
	4: _('APPROVED'),
	5: _('APPROVE_REVERSED'),
	6: _('UNAPPROVED'),
	7: _('DEPOSITED_BATCH_OPENED'),
	8: _('DEPOSITED_BATCH_CLOSED'),
	9: _('ORDER_CLOSED'),
	10: _('DELETED'),
	11: _('CREDITED_BATCH_OPENED'),
	12: _('CREDITED_BATCH_CLOSED'),
	13: _('DECLINED')
}

MUZO_PRCODE = {
	0: _('OK'),
	1: _('Field too long'),
	2: _('Field too short'),
	3: _('Incorrect content of field'),
	4: _('Field is null'),
	5: _('Missing required field'),
	11: _('Unknown merchant'),
	14: _('Duplicate order number'),
	15: _('Object not found'),
	17: _('Amount to deposit exceeds approved amount'),
	18: _('Total sum of credited amounts exceeded deposited amount'),
	20: _('Object not in valid state for operation'),
	26: _('Technical problem in connection to authorization center'),
	27: _('Incorrect order type'),
	28: _('Declined in 3D'),
	30: _('Declined in AC'),
	31: _('Wrong digest'),
	1000: _('Technical problem')
}

MUZO_SRCODE = {
	0: _('Empty'),
	1: _('ORDERNUMBER'),
	2: _('MERCHANTNUMBER'),
	6: _('AMOUNT'),
	7: _('CURRENCY'),
	8: _('DEPOSITFLAG'),
	10: _('MERORDERNUM'),
	11: _('CREDITNUMBER'),
	12: _('OPERATION'),
	18: _('BATCH'),
	22: _('ORDER'),
	24: _('URL'),
	25: _('MD'),
	26: _('DESC'),
	34: _('DIGEST'),
	1001: _("""Declined in AC, Card blocked"""),
	1002: _("""Declined in AC, Declined"""),
	1003: _("""Declined in AC, Card problem"""),
	1004: _("""Declined in AC, Technical problem in authorization process"""),
	1005: _("""Declined in AC, Account problem"""),
	3000: _("""Declined in 3D. Cardholder not authenticated in 3D. 
		   Contact your card issuer. Note: Cardholder authentication failed (wrong
		   password, transaction canceled, authentication window was closed)
		   Transaction Declined."""),
	3001: _("""Authenticated. Note: Cardholder was successfully
		   authenticated - transaction continue with
		   authorization."""),
	3002: _("""Not Authenticated in 3D. Issuer or Cardholder not participating in 3D.
		   Contact your card issuer."""),
	3004: _("""Not Authenticated in 3D. Issuer not participating or Cardholder not
		   enrolled. Contact your card issuer."""),
	3005: _("""Declined in 3D. Technical problem during Cardholder authentication.
		   Contact your card issuer"""),
	3006: _("""Declined in 3D. Technical problem during Cardholder authentication."""),
	3007: _("""Declined in 3D. Acquirer technical problem. Contact the merchant."""),
	3008: _("""Declined in 3D. Unsupported card product. Contact your card issuer""")
}

class MuzoWSError(Exception):
	pass

class MuzoWS:
	# private key file location
	priv_key = settings.MUZO_PRIV_KEY

	# password
	passwd = settings.MUZO_PASS

	# public key file location
	pub_key = settings.MUZO_PUB_KEY

	# WSDL file
    # if settings.DEBUG:
    #     wsdl_file = dirname(__file__)+'/pgwTest.xml'
    # else:
	wsdl_file = dirname(__file__)+'/pgw.xml'

	# 
	merchant_num = 57771901

	def __init__(self, order_num):
		self._server = WSDL.Proxy(self.wsdl_file)
		self._order_num = str(order_num)

	# sign data routine, returns base64 encoded digest
	def _sign(self, data):
		CS = CSignature(privkey=self.priv_key, passwd=self.passwd, pubkey=self.pub_key)
		return CS.sign(data)

	# sends orderQueryState request to WS server and returns WS object response
	def queryOrderState(self):
		d = '%s|%s' % (self.merchant_num, self._order_num)
		digest = self._sign(d)
		return self._server.queryOrderState(str(self.merchant_num), str(self._order_num), digest)

	def getOrderState(self):
		st = self.queryOrderState()
		return '%s - %s' % (st.state, MUZO_ORDER_STATES[st.state])

	def getOrderStateId(self):
		st = self.queryOrderState().state
		return int(st)

	def approveReversal(self):
		d = '%s|%s' % (self.merchant_num, self._order_num)
		digest = self._sign(d)
		response = self._server.approveReversal(str(self.merchant_num), str(self._order_num), digest)
		if response.primaryReturnCode == 0:
			return True
		else:
			return '%s - %s' % (MUZO_PRCODE.get(response.primaryReturnCode, 'Unknown'), MUZO_PRCODE.get(response.secondaryReturnCode, 'Unknown'))

	def deposit(self, amount):
		d = '%s|%s|%s' % (self.merchant_num, self._order_num, amount)
		digest = self._sign(d)
		response = self._server.deposit(str(self.merchant_num), str(self._order_num), str(self.amount), digest)
		if response.primaryReturnCode == 0:
			return True
		else:
			return '%s - %s' % (MUZO_PRCODE.get(response.primaryReturnCode, 'Unknown'), MUZO_PRCODE.get(response.secondaryReturnCode, 'Unknown'))

	def depositReversal(self):
		d = '%s|%s' % (self.merchant_num, self._order_num)
		digest = self._sign(d)
		response = self._server.depositReversal(str(self.merchant_num), str(self._order_num), digest)
		if response.primaryReturnCode == 0:
			return True
		else:
			return '%s - %s' % (MUZO_PRCODE.get(response.primaryReturnCode, 'Unknown'), MUZO_PRCODE.get(response.secondaryReturnCode, 'Unknown'))

	def credit(self, amount):
		d = '%s|%s|%s' % (self.merchant_num, self._order_num, amount)
		digest = CS._sign(d)
		response = self._server.credit(str(self.merchant_num), str(self._order_num), str(amount), digest)
		if response.primaryReturnCode == 0:
			return True
		else:
			return '%s - %s' % (MUZO_PRCODE.get(response.primaryReturnCode, 'Unknown'), MUZO_PRCODE.get(response.secondaryReturnCode, 'Unknown'))

	def creditReversal(self):
		d = '%s|%s' % (self.merchant_num, self._order_num)
		digest = self._sign(d)
		response = self._server.creditReversal(str(self.merchant_num), str(self._order_num), digest)
		if response.primaryReturnCode == 0:
			return True
		else:
			return '%s - %s' % (MUZO_PRCODE.get(response.primaryReturnCode, 'Unknown'), MUZO_PRCODE.get(response.secondaryReturnCode, 'Unknown'))

	def orderClose(self):
		d = '%s|%s' % (self.merchant_num, self._order_num)
		digest = self._sign(d)
		response = self._server.orderClose(str(self.merchant_num), str(self._order_num), digest)
		if response.primaryReturnCode == 0:
			return True
		else:
			return '%s - %s' % (MUZO_PRCODE.get(response.primaryReturnCode, 'Unknown'), MUZO_PRCODE.get(response.secondaryReturnCode, 'Unknown'))

	def delete(self):
		d = '%s|%s' % (self.merchant_num, self._order_num)
		digest = self._sign(d)
		response = self._server.delete(str(self.merchant_num), str(self._order_num), digest)
		if response.primaryReturnCode == 0:
			return True
		else:
			return '%s - %s' % (MUZO_PRCODE.get(response.primaryReturnCode, 'Unknown'), MUZO_PRCODE.get(response.secondaryReturnCode, 'Unknown'))

	def batchClose(self):
		d = '%s|%s' % (self.merchant_num, self._order_num)
		digest = self._sign(d)
		response = self._server.batchClose(str(self.merchant_num), str(self._order_num), digest)
		if response.primaryReturnCode == 0:
			return True
		else:
			return '%s - %s' % (MUZO_PRCODE.get(response.primaryReturnCode, 'Unknown'), MUZO_PRCODE.get(response.secondaryReturnCode, 'Unknown'))
