from django.conf import settings
from django.db import models
from django.utils.translation import get_language
from django.db.models.signals import post_init
from django.core.urlresolvers import reverse

from datetime import datetime
from urllib import urlencode
from signature import CSignature

from signals import muzo_successful, muzo_failed

# required, which values should be send; options full, short
QUERY_OPTION = 'FULL'

# private key file location
PRIV_KEY = settings.MUZO_PRIV_KEY

# password
PASSWD = settings.MUZO_PASS

# public key file location
PUB_KEY = settings.MUZO_PUB_KEY

# required, merchant number
MERCHANT_NUM = settings.MUZO_MERCHANT_NUM

# required, operation option, default 'CREATE_ORDER'    
OPERATION = 'CREATE_ORDER'

# required, currency code, default 203 - CZK
CURRENCY = None

# required, 0 - payment not required, 1 - payment required  
DEPOSIT_FLAG = 0

# required, full url address with protocol where send data for card verification 
#request_url = 'https://pay.muzo.com/test/order.do'
REQUEST_URL = settings.MUZO_REQUEST_URL

# required, full url address with protocol where payment result should be sent 
# RETURN_URL = settings.BASE_URL + get_language() + settings.MUZO_RESPONSE_URL
RETURN_URL = settings.BASE_URL.strip('/') + settings.MUZO_RESPONSE_URL

# not required, description, ascii chars from 0x20 - 0x7E
DESCRIPTION = 'Purchase'        


class Response(models.Model):
    OPERATION = models.CharField(max_length=20)
    ORDERNUMBER = models.CharField(max_length=15)
    MERORDERNUM = models.CharField(max_length=16, blank=True, null=True)
    MD = models.CharField(max_length=30, blank=True, null=True)
    PRCODE = models.IntegerField(max_length=5)
    SRCODE = models.IntegerField(max_length=5)
    RESULTTEXT = models.TextField()
    DIGEST = models.TextField()
    VERIFICATION = models.BooleanField(default=False)
    DATE = models.DateTimeField(default=datetime.now, editable=False)


    def save(self, *args, **kwargs):
        self.verify()
        super(Response, self).save(*args, **kwargs)
        self.send_signals()

    def __unicode__(self):
        return u'%s' % (self.ORDERNUMBER,)

    def verify(self):
        self.VERIFICATION = self._signature.verify(self.digest_data, self.DIGEST)
        return self.VERIFICATION
    
    @property
    def is_flagged(self):
        return not (self.PRCODE == self.SRCODE == 0)

    @property
    def digest_data(self):
        return "%s|%s|%s|%s|%s|%s|%s" % (
                    self.OPERATION, self.ORDERNUMBER, self.MERORDERNUM, 
                    self.MD, self.PRCODE, self.SRCODE, self.RESULTTEXT 
                )
    
    def send_signals(self):
        if self.is_flagged:
            muzo_successful.send(sender=self)
        else:
            muzo_failed.send(sender=self)


class Request(models.Model):
    AMOUNT = models.IntegerField(max_length=12, blank=True, null=True)
    OPERATION = models.CharField(default=OPERATION, max_length=20, blank=True, null=True)
    ORDERNUMBER = models.CharField(max_length=15, blank=True, null=True)
    DEPOSITFLAG = models.IntegerField(default=DEPOSIT_FLAG, max_length=1, blank=True, null=True)
    MERCHANTNUMBER = models.IntegerField(default=MERCHANT_NUM, max_length=11, blank=True, null=True)
    URL = models.TextField(blank=True, null=True)
    DIGEST = models.TextField(blank=True, null=True)
    CURRENCY = models.IntegerField(default=CURRENCY, max_length=4, blank=True, null=True)
    MERORDERNUM = models.CharField(max_length=16, blank=True, null=True)
    DESCRIPTION = models.TextField(default=DESCRIPTION, blank=True, null=True)
    MD = models.CharField(max_length=30, blank=True, null=True)
    DATE = models.DateTimeField(default=datetime.now, editable=False)
    

    def save(self):
        if not self.id:
            # We need to reset current language
            # if getattr(settings, 'BASE_URL', False) and getattr(settings, 'MUZO_RESPONSE_URL', False):
            if not self.URL:
                self.URL = RETURN_URL
            super(Request, self).save()
            self.ORDERNUMBER = self.id
        
        self.DIGEST = self._signature.sign(self.digest_data())
        super(Request, self).save()

    def __unicode__(self):
        return u'%s' % (self.ORDERNUMBER,)

    def digest_data(self):
        if QUERY_OPTION == 'SHORT':
            return "%s|%s|%s|%s|%s|%s" % (
                        self.MERCHANTNUMBER, self.OPERATION, self.ORDERNUMBER, 
                        self.AMOUNT, self.DEPOSITFLAG, self.URL
                    )
        elif QUERY_OPTION == 'FULL':
            return "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % (
                        self.MERCHANTNUMBER, self.OPERATION, self.ORDERNUMBER, self.AMOUNT, 
                        self.CURRENCY, self.DEPOSITFLAG, self.MERORDERNUM, self.URL,
                        self.DESCRIPTION, self.MD
                    )
        return None

    def get_request_url(self, query_option=False):
        if not self.id:
            self.save()

        if QUERY_OPTION == 'SHORT':
            self.query = {
                        'AMOUNT': self.AMOUNT,
                        'OPERATION': self.OPERATION, 
                        'ORDERNUMBER': self.ORDERNUMBER, 
                        'DEPOSITFLAG': self.DEPOSITFLAG,
                        'MERCHANTNUMBER': self.MERCHANTNUMBER,
                        'URL': self.URL, 
                        'DIGEST': self.DIGEST
            }

        elif QUERY_OPTION == 'FULL':
            self.query = {
                        'AMOUNT': self.AMOUNT,
                        'OPERATION': self.OPERATION, 
                        'ORDERNUMBER': self.ORDERNUMBER, 
                        'DEPOSITFLAG': self.DEPOSITFLAG,
                        'MERCHANTNUMBER': self.MERCHANTNUMBER,
                        'URL': self.URL, 
                        'DIGEST': self.DIGEST,
                        'CURRENCY': self.CURRENCY,
                        'MERORDERNUM': self.MERORDERNUM,
                        'DESCRIPTION': self.DESCRIPTION,
                        'MD': self.MD
            }

        return "%s?%s" % (REQUEST_URL, urlencode(self.query))


def signature(instance, **kwargs):
    instance._signature = CSignature(PRIV_KEY, PASSWD, PUB_KEY)


post_init.connect(signature, sender=Request)
post_init.connect(signature, sender=Response)