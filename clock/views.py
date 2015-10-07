from datetime import datetime, timedelta, date
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import login
from django.core.context_processors import csrf
from django.core.mail import send_mail, EmailMessage
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.template.response import TemplateResponse
from clock.models import * 
from clock.forms import *
from clock.controllers import *

def login_success(request):
	if request.user.groups.filter(name="Supervisor").exists():
		return redirect('superprofile')
	else:
		return redirect('user-profile')

def json_in_employees(request):
	return HttpResponse(json_employees('in'), 'application/json')

@login_required
@user_passes_test(is_employee, login_url='/login/')
def profile(request):
	if request.user.groups.filter(name='Supervisor').count() == 1:
		return redirect('superprofile')
	elif request.user.groups.filter(name='Help Desk Staff').count == 0 and request.user.groups.filter(name='Supervisor').count == 0:
		logout(request)
		return TemplateResponse(request, 'timeclock/forbidden.html', {'user': request.user})
	context = RequestContext(request)
	employee = Employee.objects.get(user=request.user)
	now = datetime.now() #- timedelta(hours=10)
	in_form = ClockInForm(initial={'time_in': now.time(), 'time_out': now.time()})
	out_form = ClockOutForm(initial={'time_out': now.time()})
	in_employees = get_clocked_in_employees()
	
	errors = False
	
	if request.method == 'POST':
		if request.POST.get('action', False) == 'clock_in':
			form = ClockInForm(request.POST)
			if form.is_valid():
				event = ClockEvent()
				event.employee = employee
				event.message = form.cleaned_data['message']
				event.time_in = form.cleaned_data['time_in']
				event.time_out = form.cleaned_data['time_out']
				if can_clock_in(event):
					errors = False
					event.save()
					employee.clocked_in = True
					employee.last_clocked_in = datetime.combine(event.date, event.time_in)
					employee.last_clocked_out = datetime.combine(event.date, event.time_out)
					employee.last_message = event.message
					employee.save()
				else:
					errors = True

		elif request.POST.get('action', False) == 'clock_out':
			event = ClockEvent.objects.filter(employee=employee).order_by("-created")[0]
			form = ClockOutForm(request.POST)
			if form.is_valid():
				event.message = form.cleaned_data['message']
				event.time_out = form.cleaned_data['time_out']
				event.save()
				employee.clocked_in = False
				employee.last_clocked_out = datetime.combine(event.date, event.time_out)
				employee.last_message = event.message
				employee.save()
	events = ClockEvent.objects.filter(employee=employee).order_by("-created")
	return render_to_response('clock/profile.html', {'employee': employee,'events': events,'user': request.user, 'out_form': out_form, 'in_form': in_form, 'clocked_in_employees': in_employees, 'errors': errors }, context)

@login_required
def superprofile(request):
	if request.user.groups.filter(name='Supervisor').count() == 0:
		return TemplateResponse(request, 'timeclock/forbidden.html', {'user': request.user})
	else:
		admin = request.user
		context = RequestContext(request)
		employees = Employee.objects.all().order_by('user').order_by('-clocked_in').filter(user__groups__name='Help Desk Staff')
		clocked_in_employees = get_clocked_in_employees()
		return render_to_response('clock/superprofile.html', {'employees': employees, 'admin': admin, 'clocked_in_employees': clocked_in_employees, 'user': request.user })

@login_required
def super_clockevent_history(request):
	if request.user.groups.filter(name="Supervisor").count() == 0:
		return TempateResponse(request, 'timeclock/forbidden.html', {'user': request.user})
	else:
		context = RequestContext(request)
		events = ClockEvent.objects.all()
		now = datetime.now()
		start_date = (now - timedelta(weeks=2)).date()
		end_date = now.date()
		history_form = FilterClockEventForm(initial={'start_date': start_date, 'end_date': end_date})
		
		if request.method == 'POST':
			history_form = FilterClockEventForm(request.POST)
			if history_form.is_valid():
				start_date = history_form.cleaned_data['start_date']
				end_date = history_form.cleaned_data['end_date']
		events = get_clock_events_between(start_date, end_date)
		hour_total = 0.0
		total_cost = 0.0
		for e in events:
			hour_amount = e.time_worked().total_seconds()/3600
			hour_total += hour_amount
			total_cost += hour_amount * e.employee.pay_rate
			
		return render_to_response('clock/superclockhistory.html', {'events': events, 'hour_total': hour_total, 'total_cost': total_cost, 'history_form': history_form }, context)

@login_required
def employee_history(request, employee_id):
	if request.user.groups.filter(name="Supervisor").count == 0:
		return TemplateResponse(request, 'timeclock/forbidden.html', {'user': request.user})
	context = RequestContext(request)
	employee = Employee.objects.get(pk=employee_id)
	events = ClockEvent.objects.filter(employee=employee)
	now = datetime.now()
	start_date = (now - timedelta(weeks=2)).date()
	end_date = now.date()
	history_form = FilterClockEventForm(initial={'start_date': start_date, 'end_date': end_date})
	
	if request.method == 'POST':
		history_form = FilterClockEventForm(request.POST)
		if history_form.is_valid():
			start_date = history_form.cleaned_data['start_date']
			end_date = history_form.cleaned_data['end_date']
	events = get_clock_events_between(start_date, end_date).filter(employee=employee)
	hour_total = 0.0
	total_cost = 0.0
	for e in events:
		hour_amount = e.time_worked().total_seconds()/3600
		hour_total += hour_amount
		total_cost += hour_amount * e.employee.pay_rate
	
	return render_to_response('clock/employeehistory.html', {'events': events, 'hour_total': hour_total, 'total_cost': total_cost, 'history_form': history_form, 'employee': employee }, context)

@login_required
@user_passes_test(is_employee, login_url='/login/')
def clockevent_history(request):
	if request.user.groups.filter(name='Supervisor').count() == 1:
		return HttpResponseRedirect('/super-clockevent-history/')
	context = RequestContext(request)
	employee = Employee.objects.get(user=request.user)
	now = datetime.now()
	start_date = (now - timedelta(weeks=2)).date()
	end_date = now.date()
	history_form = FilterClockEventForm(initial={'start_date': start_date,'end_date': end_date})
	
	if request.method == 'POST':
		history_form = FilterClockEventForm(request.POST)
		if history_form.is_valid():
			start_date = history_form.cleaned_data['start_date']
			end_date = history_form.cleaned_data['end_date']
	events = get_clock_events_between(start_date, end_date).filter(employee=employee)
	total_time = timedelta(0)
	for e in events:
		total_time += e.time_worked()
	hour_total = total_time.total_seconds()/3600
	timecard = populate_timesheet(employee, start_date)
	link = timecard.name.split('k/')[1]
	return render_to_response('clock/clockhistory.html', {'timecard': link,'employee': employee, 'events': events, 'user': request.user,'time_worked': hour_total, 'history_form': history_form }, context)

@login_required
@user_passes_test(is_employee, login_url='/login/')
def edit_profile(request):
	context = RequestContext(request)
	edited = False
	valid = True
	if request.method == 'POST':
		user_form = UpdateUserForm(request.POST, instance=request.user)
		employee_form = EmployeeForm(request.POST, request.FILES)
		if user_form.is_valid() and employee_form.is_valid():
			user = request.user
			user.set_password(user.password)
			user.first_name = user_form.cleaned_data['first_name']
			user.last_name = user_form.cleaned_data['last_name']
			user.email = user_form.cleaned_data['email']
			user.save()
			
			employee = Employee.objects.get(user=request.user)
			if 'profile_pic' in request.FILES:
				employee.profile_pic = employee_form.files['profile_pic']
				pic = request.FILES['profile_pic']
				mail = EmailMessage('[Django Timeclock] New Profile Picture for ' + user.first_name, '/media/profile_images/' + employee.profile_pic.name, 'django-timeclock@engineering.ucsb.edu', [])
				mail.attach(pic.name, pic.read(), pic.content_type)
				mail.send()
			employee.save()

			edited = True
			return render_to_response('clock/editprofile.html', {'user_form': user_form, 'employee_form': employee_form, 'edited': edited, 'valid': valid,}, context)
		else: valid = False
	else:
		user_form = UpdateUserForm(instance=request.user)
		employee_form = EmployeeForm()
	return render_to_response('clock/editprofile.html', {'user_form': user_form, 'employee_form': employee_form, 'edited': edited, 'valid': valid,}, context)

def index(request):
	context = RequestContext(request)
	clock_employees = Employee.objects.order_by('user__first_name').filter(user__groups__name='Help Desk Staff')
	user = request.user
	if user.is_authenticated:
		response = render_to_response('clock/home.html', {'user': user, 'clock_employees': clock_employees})
	else:
		response = render_to_response('clock/home.html', {'clock_employees': clock_employees})
	return response

def register(request):
	context = RequestContext(request)
	# Set to True upon successful registration
	registered = False

	if request.method == 'POST':
		user_form = UserForm(data=request.POST)
		employee_form = EmployeeForm(data=request.POST)
		# If these forms are valid
		if user_form.is_valid() and employee_form.is_valid():
			# Save user form data to database
			user = user_form.save()
			
			# Hash the password so we can update
			user.set_password(user.password)
			user.save()
			
			#print user.get_full_name()
				
			employee = employee_form.save(commit=False)
			employee.user = user
		
			if 'profile_pic' in request.FILES:
				employee.profile_pic = request.files['profile_pic']
			employee.save()
			registered = True # Registration was successful
			return render_to_response('timeclock/register.html',
				{'user_form': user_form, 'employee_form': employee_form, 'registered': registered,'user': request.user},
				context)
	# Not an HTTP POST, so render blank forms
	else:
		user_form = UserForm()
		employee_form = EmployeeForm()
	
	args = {}
	args.update(csrf(request))
	return render(request, 'timeclock/register.html',
		{'user_form': user_form, 'employee_form': employee_form, 'registered': registered,'user': request.user,})
