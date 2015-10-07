from datetime import datetime, timedelta
from clock.models import *
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms.extras.widgets import SelectDateWidget
from clock.models import ClockEvent
from clock.widgets import SelectTimeWidget
from django import forms

def validate_username_unique(value):
	"""Custom validator for user uniqueness"""
	if User.objects.filter(username=value).exists():
		raise ValidationError(u'That username is taken.')

class UserForm(forms.ModelForm):
	username = forms.CharField(validators=[validate_username_unique])
	password = forms.CharField(widget=forms.PasswordInput)
	password_confirm = forms.CharField(widget=forms.PasswordInput)
	
	def clean_password_confirm(self):
		"""Required custom validation for the form."""
		# super(UserForm,self).clean()
		if 'password' in self.cleaned_data and 'password_confirm' in self.cleaned_data:
			if self.cleaned_data['password'] != self.cleaned_data['password_confirm']:
				self._errors['password'] = u'* Passwords must match.'
				self._errors['password_confirm'] = u'* Passwords must match.'
		return self.cleaned_data
		
	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'email', 'password',)

def auth(u, p):
	return authenticate(username=u, password=p)

class UpdateUserForm(forms.ModelForm):
	username = forms.CharField(label="Your Current Username")
	password = forms.CharField(widget=forms.PasswordInput, label="Your Current Password")
	
	def clean(self):
		cleaned_data = super(UpdateUserForm, self).clean()
		form_password = cleaned_data.get('password')
		form_username = cleaned_data.get('username')
		
		if form_password and form_username:
			form_user = auth(form_username, form_password)
			if form_user is None:
				self.errors['password'] = u'You have entered an incorrect password.'
		return self.cleaned_data
			
	
	class Meta:
		model = User
		fields = ('first_name', 'last_name', 'email', 'username', 'password')

class EmployeeForm(forms.ModelForm):
	profile_pic = forms.FileField(widget=forms.FileInput, required=False)
	class Meta:
		model = Employee
		fields = ('profile_pic',)

class ClockInForm(forms.ModelForm):
	time_in = forms.TimeField(widget=SelectTimeWidget(minute_step=15, second_step=60, twelve_hr=True), label="Time In")
	time_out = forms.TimeField(widget=SelectTimeWidget(minute_step=15, second_step=60, twelve_hr=True), label="Expected Time Out")
	message = forms.CharField(max_length=500, widget=forms.TextInput(attrs={'class':'form-control'}), label="What will you be doing today?")
	
	class Meta:
		model = ClockEvent
		exclude = ('employee','date','created')

class ClockOutForm(forms.ModelForm):
	time_out = forms.TimeField(widget=SelectTimeWidget(minute_step=15, second_step=60, twelve_hr=True), label="Time Out")
	message = forms.CharField(max_length=500, widget=forms.TextInput(attrs={'class':'form-control'}), label="What did you do today?")
	
	class Meta:
		model = ClockEvent
		exclude = ('employee','time_in','date','created')

class FilterClockEventForm(forms.Form):
	start_date = forms.DateField(widget=SelectDateWidget, label="Start Date")
	end_date   = forms.DateField(widget=SelectDateWidget, label="End Date")
