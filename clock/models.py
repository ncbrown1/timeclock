from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User

class Employee(models.Model):
	user = models.OneToOneField(User)
	
	clocked_in = models.BooleanField(default=False)
	last_clocked_in = models.DateTimeField(blank=True, null=True)
	last_clocked_out = models.DateTimeField(blank=True, null=True)
	last_message = models.CharField(max_length=500, blank=True, null=True, default="")
	pay_rate = models.FloatField(default='15.00')
	profile_pic = models.ImageField(upload_to='profile_images', default="/static/profile_images/default-pp.png", blank=True, null=True)
	
	def __unicode__(self):
		return self.user.username

	class Meta:
		verbose_name = 'Employee'
		verbose_name_plural = 'Employees'

class ClockEvent(models.Model):
	employee = models.ForeignKey(Employee, unique=True)
	message = models.TextField(max_length=500)
	date = models.DateField(auto_now_add=True)
	time_in = models.TimeField()
	time_out = models.TimeField()
	created = models.DateTimeField(auto_now_add=True)
	
	def time_worked(self):
		dt = datetime.combine(self.date, self.time_out) - datetime.combine(self.date, self.time_in)
		return timedelta(seconds=dt.total_seconds()%(24*60*60))
	
	def __unicode__(self):
		return u'%s - %s - %s - %s' % (self.employee, self.date, self.time_in, self.time_out)
