from django.forms import ModelForm
from models import *

class ReqForm(ModelForm):
	class Meta:
		model = Request

class ResForm(ModelForm):
	class Meta:
		model = Response
