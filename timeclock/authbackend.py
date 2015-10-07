from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class ClockBackend(ModelBackend):
	
	def authenticate(self, username=None, password=None, **kwargs):
		UserModel = get_user_model()
		if username is None:
			username = kwargs.get(UserModel.USERNAME_FIELD)
		try:
			user = UserModel._default_manager.get_by_natural_key(username)
			if user.check_password(password) and (user.groups.filter(name='Supervisor').count() == 1 or user.groups.filter(name='Help Desk Staff').count() == 1):
				return user
		except UserModel.DoesNotExist:
			UserModel().set_password(password)
