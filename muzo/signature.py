from M2Crypto import RSA
from base64 import *
from urllib import unquote
import hashlib
import sys

class CSignature:	
	def __init__(self, privkey, passwd, pubkey):
		self.passwd = passwd		
		self.priv_key = RSA.load_key(privkey,self.pp_callback)
		self.pub_key = RSA.load_pub_key(pubkey)

	def pp_callback(self, *args):
		return self.passwd

	def sign(self, data):
		data = hashlib.sha1(data).digest()
		return b64encode(self.priv_key.sign(data))

	def verify(self, data, signature):
		digest = hashlib.sha1(data).digest()
		signature = unquote(signature)
		signature = b64decode(signature)
		try:
			return self.pub_key.verify(data, signature)
		except:
			return False