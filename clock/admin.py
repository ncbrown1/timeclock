from django.contrib import admin
from clock.models import *

class ClockEventAdmin(admin.ModelAdmin):
	list_display = ['employee','date','time_in','time_out','time_worked','message', 'created']
	list_filter = ['employee', 'date']

admin.site.register(ClockEvent, ClockEventAdmin)
admin.site.register(Employee)
