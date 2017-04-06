import rsa
import sys

from base64 import *
from urllib import unquote

class CSignature:
    def __init__(self, privkey, passwd, pubkey):
        self.passwd = passwd

        with open(privkey) as priv_key:
            priv_key_data = priv_key.read()

        self.priv_key = rsa.PrivateKey.load_pkcs1(priv_key_data)

        with open(pubkey) as pub_key:
            pub_key_data = pub_key.read()

        self.pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(pub_key_data)

    def sign(self, data):
        return b64encode(rsa.sign(data, self.priv_key, 'SHA-1'))

    def verify(self, data, signature):
        signature = unquote(signature)
        signature = b64decode(signature)
        try:
            return rsa.verify(data, signature, self.pub_key)
        except:
            return False
