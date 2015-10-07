import json
import os
from datetime import datetime, date, timedelta
from django.conf import settings
from clock.models import ClockEvent, Employee
from string import Template
import tempfile

def is_helpdesk_staff(user):
        if user:
                return user.groups.filter(name='Help Desk Staff').count() == 1
        return False

def is_supervisor(user):
	if user:
		return user.groups.filter(name='Supervisor').count() == 1
	return False

def is_employee(user):
	return is_helpdesk_staff(user) or is_supervisor(user)

def is_supervisor(user):
        if user:
                return user.groups.filter(name='Supervisor').count() == 1
        return False

def get_clocked_in_employees():
        return Employee.objects.filter(clocked_in=True).order_by('-last_clocked_in')

def get_clocked_out_employees():
        return Employee.objects.filter(clocked_in=False).order_by('last_clocked_out').filter(user__groups__name='Help Desk Staff')

def get_clock_events_between(date1, date2):
        return ClockEvent.objects.filter(date__range=[date1, date2]).order_by('-created')

def json_employees(in_out_or_all):
        if in_out_or_all == 'in':
                query = get_clocked_in_employees()
        elif in_out_or_all == 'out':
                query = get_clocked_out_employees()
        elif in_out_or_all == 'all':
                query = Employee.objects.all()
        else:
                return json.dumps(['Invalid input'])
        data = []
        for row in query:
                data.append({'id': row.pk, 'username': row.user.username, 'first_name': row.user.first_name, 'last_name': row.user.last_name, 'email': row.user.email, 'clocked_in': row.clocked_in})
        data_as_json = json.dumps(data, sort_keys=True, indent=2)
        return data_as_json

def time_is_after(t1, t2): # arg1 is time in question, arg2 is time in reference
        day = datetime.now().date()
        d1 = datetime.combine(day, t1)
        d2 = datetime.combine(day, t2)
        td = d1 - d2
        if td.total_seconds() > 0:
                return True
        else: return False

def time_is_before(t1, t2): # arg1 is time in question, arg2 is time in reference
        day = datetime.now().date()
        d1 = datetime.combine(day, t1)
        d2 = datetime.combine(day, t2)
        td = d1 - d2
        if td.total_seconds() < 0:
                return True
        else: return False

def time_is_equal(t1, t2):
        day = datetime.now().date()
        d1 = datetime.combine(day, t1)
        d2 = datetime.combine(day, t2)
        td = d1 - d2
        if td.total_seconds() == 0:
                return True
        else: return False      

def can_clock_in(event):
        events = ClockEvent.objects.filter(employee=event.employee).filter(date=datetime.now().date())
        for e in events:
                if time_is_after(event.time_in, e.time_in) and time_is_before(event.time_in, e.time_out):
                        return False
                elif time_is_before(event.time_in, e.time_in) and time_is_after(event.time_out, e.time_out): 
                        return False
                elif time_is_before(event.time_in, e.time_in) and time_is_after(event.time_out, e.time_in) and time_is_before(event.time_out, e.time_out):
                        return False
                elif time_is_equal(event.time_in, e.time_in):
                        return False
        return True

def find_closest_sunday(time):
	back = time
	fwd = time
	while back.strftime('%A') != 'Sunday':
		back = back - timedelta(days=1)
	while fwd.strftime('%A') != 'Sunday':
		fwd = fwd + timedelta(days=1)
	d_back = time-back
	d_fwd = fwd-time
	if d_back > d_fwd:
		return fwd
	else:
		return back

def split_into_day_lists(employee,start_date):
	start = find_closest_sunday(start_date)
	data = []	
	s = start
	while s != (start+timedelta(weeks=2)):
		evs = ClockEvent.objects.filter(date=s).filter(employee=employee)
		d = []
		for e in evs:
			d.append(e)
		data.append(d)
		s = s + timedelta(days=1)
	return data

def populate_timesheet(employee, start_date):
	times = dict(
		Name="", PeriodStart="", PeriodEnd="",

		SunIn1="",SunIn2="",SunIn3="",SunIn4="",
		SunOut1="",SunOut2="",SunOut3="",SunOut4="",
		TotalSun1="", TotalSun2="",

		MonIn1="",MonIn2="",MonIn3="",MonIn4="",
		MonOut1="",MonOut2="",MonOut3="",MonOut4="",
		TotalMon1="", TotalMon2="",

		TueIn1="",TueIn2="",TueIn3="",TueIn4="",
		TueOut1="",TueOut2="",TueOut3="",TueOut4="",
		TotalTue1="", TotalTue2="",

		WedIn1="",WedIn2="",WedIn3="",WedIn4="",
		WedOut1="",WedOut2="",WedOut3="",WedOut4="",
		TotalWed1="", TotalWed2="",

		ThurIn1="",ThurIn2="",ThurIn3="",ThurIn4="",
		ThurOut1="",ThurOut2="",ThurOut3="",ThurOut4="",
		TotalThur1="", TotalThur2="",

		FriIn1="",FriIn2="",FriIn3="",FriIn4="",
		FriOut1="",FriOut2="",FriOut3="",FriOut4="",
		TotalFri1="", TotalFri2="",

		SatIn1="",SatIn2="",SatIn3="",SatIn4="",
		SatOut1="",SatOut2="",SatOut3="",SatOut4="",
		TotalSat1="", TotalSat2="",
		
		TotalAll="",
	)
	d = split_into_day_lists(employee,start_date)
	su1t = timedelta(0)
	mo1t = timedelta(0)
	tu1t = timedelta(0)
	we1t = timedelta(0)
	th1t = timedelta(0)
	fr1t = timedelta(0)
	sa1t = timedelta(0)
	su2t = timedelta(0)
	mo2t = timedelta(0)
	tu2t = timedelta(0)
	we2t = timedelta(0)
	th2t = timedelta(0)
	fr2t = timedelta(0)
	sa2t = timedelta(0)
	try:
		if d[0][0]: 
			times['SunIn1'] = d[0][0].time_in.strftime('%I:%M %p')
			times['SunOut1'] = d[0][0].time_out.strftime('%I:%M %p')
			su1t += d[0][0].time_worked()
	except:
		pass
	try:
		if d[0][1]:
			times['SunIn2'] = d[0][1].time_in.strftime('%I:%M %p')
			times['SunOut2'] = d[0][1].time_out.strftime('%I:%M %p')
			su1t += d[0][1].time_worked()
	except:
		pass
	try:
		if d[1][0]: 
			times['MonIn1'] = d[1][0].time_in.strftime('%I:%M %p')
			times['MonOut1'] = d[1][0].time_out.strftime('%I:%M %p')
			mo1t += d[1][0].time_worked()
	except:
		pass
	try:
		if d[1][1]:
			times['MonIn2'] = d[1][1].time_in.strftime('%I:%M %p')
			times['MonOut2'] = d[1][1].time_out.strftime('%I:%M %p')
			mo1t += d[1][1].time_worked()
	except:
		pass
	try:
		if d[2][0]: 
			times['TueIn1'] = d[2][0].time_in.strftime('%I:%M %p')
			times['TueOut1'] = d[2][0].time_out.strftime('%I:%M %p')
			tu1t += d[2][0].time_worked()
	except:
		pass
	try:
		if d[2][1]:
			times['TueIn2'] = d[2][1].time_in.strftime('%I:%M %p')
			times['TueOut2'] = d[2][1].time_out.strftime('%I:%M %p')
			tu1t += d[2][1].time_worked()
	except:
		pass
	try:
		if d[3][0]: 
			times['WedIn1'] = d[3][0].time_in.strftime('%I:%M %p')
			times['WedOut1'] = d[3][0].time_out.strftime('%I:%M %p')
			we1t += d[3][0].time_worked()
	except:
		pass
	try:
		if d[3][1]:
			times['WedIn2'] = d[3][1].time_in.strftime('%I:%M %p')
			times['WedOut2'] = d[3][1].time_out.strftime('%I:%M %p')
			weu1t += d[3][1].time_worked()
	except:
		pass
	try:
		if d[4][0]: 
			times['ThurIn1'] = d[4][0].time_in.strftime('%I:%M %p')
			times['ThurOut1'] = d[4][0].time_out.strftime('%I:%M %p')
			th1t += d[4][0].time_worked()
	except:
		pass
	try:
		if d[4][1]:
			times['ThurIn2'] = d[4][1].time_in.strftime('%I:%M %p')
			times['ThurOut2'] = d[4][1].time_out.strftime('%I:%M %p')
			th1t += d[4][1].time_worked()
	except:
		pass
	try:
		if d[5][0]: 
			times['FriIn1'] = d[5][0].time_in.strftime('%I:%M %p')
			times['FriOut1'] = d[5][0].time_out.strftime('%I:%M %p')
			fr1t += d[5][0].time_worked()
	except:
		pass
	try:
		if d[5][1]:
			times['FriIn2'] = d[5][1].time_in.strftime('%I:%M %p')
			times['FriOut2'] = d[5][1].time_out.strftime('%I:%M %p')
			fr1t += d[5][1].time_worked()
	except:
		pass
	try:
		if d[6][0]: 
			times['SatIn1'] = d[6][0].time_in.strftime('%I:%M %p')
			times['SatOut1'] = d[6][0].time_out.strftime('%I:%M %p')
			sa1t += d[6][0].time_worked()
	except:
		pass
	try:
		if d[6][1]:
			times['SatIn2'] = d[6][1].time_in.strftime('%I:%M %p')
			times['SatOut2'] = d[6][1].time_out.strftime('%I:%M %p')
			sa1t += d[6][1].time_worked()
	except:
		pass
	try:
		if d[7][0]: 
			times['SunIn3'] = d[7][0].time_in.strftime('%I:%M %p')
			times['SunOut3'] = d[7][0].time_out.strftime('%I:%M %p')
			su2t += d[7][0].time_worked()
	except:
		pass
	try:
		if d[7][1]:
			times['SunIn4'] = d[7][1].time_in.strftime('%I:%M %p')
			times['SunOut4'] = d[7][1].time_out.strftime('%I:%M %p')
			su2t += d[7][1].time_worked()
	except:
		pass
	try:
		if d[8][0]: 
			times['MonIn3'] = d[8][0].time_in.strftime('%I:%M %p')
			times['MonOut3'] = d[8][0].time_out.strftime('%I:%M %p')
			mo2t += d[8][0].time_worked()
	except:
		pass
	try:
		if d[8][1]:
			times['MonIn4'] = d[8][1].time_in.strftime('%I:%M %p')
			times['MonOut4'] = d[8][1].time_out.strftime('%I:%M %p')
			mo2t += d[8][1].time_worked()
	except:
		pass
	try:
		if d[9][0]: 
			times['TueIn3'] = d[9][0].time_in.strftime('%I:%M %p')
			times['TueOut3'] = d[9][0].time_out.strftime('%I:%M %p')
			tu2t += d[9][0].time_worked()
	except:
		pass
	try:
		if d[9][1]:
			times['TueIn4'] = d[9][1].time_in.strftime('%I:%M %p')
			times['TueOut4'] = d[9][1].time_out.strftime('%I:%M %p')
			tu2t += d[9][1].time_worked()
	except:
		pass
	try:
		if d[10][0]: 
			times['WedIn3'] = d[10][0].time_in.strftime('%I:%M %p')
			times['WedOut3'] = d[10][0].time_out.strftime('%I:%M %p')
			we2t += d[10][0].time_worked()
	except:
		pass
	try:
		if d[10][1]:
			times['WedIn4'] = d[10][1].time_in.strftime('%I:%M %p')
			times['WedOut4'] = d[10][1].time_out.strftime('%I:%M %p')
			we2t += d[10][1].time_worked()
	except:
		pass
	try:
		if d[11][0]: 
			times['ThurIn3'] = d[11][0].time_in.strftime('%I:%M %p')
			times['ThurOut3'] = d[11][0].time_out.strftime('%I:%M %p')
			th2t += d[11][0].time_worked()
	except:
		pass
	try:
		if d[11][1]:
			times['ThurIn4'] = d[11][1].time_in.strftime('%I:%M %p')
			times['ThurOut4'] = d[11][1].time_out.strftime('%I:%M %p')
			th2t += d[11][1].time_worked()
	except:
		pass
	try:
		if d[12][0]: 
			times['FriIn3'] = d[12][0].time_in.strftime('%I:%M %p')
			times['FriOut3'] = d[12][0].time_out.strftime('%I:%M %p')
			fr2t += d[12][0].time_worked()
	except:
		pass
	try:
		if d[12][1]:
			times['FriIn4'] = d[12][1].time_in.strftime('%I:%M %p')
			times['FriOut4'] = d[12][1].time_out.strftime('%I:%M %p')
			fr2t += d[12][1].time_worked()
	except:
		pass
	try:
		if d[13][0]: 
			times['SatIn3'] = d[14][0].time_in.strftime('%I:%M %p')
			times['SatOut3'] = d[14][0].time_out.strftime('%I:%M %p')
			sa2t += d[13][0].time_worked()
	except:
		pass
	try:
		if d[13][1]:
			times['SatIn4'] = d[14][1].time_in.strftime('%I:%M %p')
			times['SatOut4'] = d[14][1].time_out.strftime('%I:%M %p')
			sa2t += d[13][1].time_worked()
	except:
		pass
	times['TotalSun1'] = su1t.total_seconds()/3600 
	times['TotalMon1'] = mo1t.total_seconds()/3600
	times['TotalTue1'] = tu1t.total_seconds()/3600
	times['TotalWed1'] = we1t.total_seconds()/3600
	times['TotalThur1'] = th1t.total_seconds()/3600
	times['TotalFri1'] = fr1t.total_seconds()/3600
	times['TotalSat1'] = sa1t.total_seconds()/3600
	times['TotalSun2'] = su2t.total_seconds()/3600
	times['TotalMon2'] = mo2t.total_seconds()/3600
	times['TotalTue2'] = tu2t.total_seconds()/3600
	times['TotalWed2'] = we2t.total_seconds()/3600
	times['TotalThur2'] = th2t.total_seconds()/3600
	times['TotalFri2'] = fr2t.total_seconds()/3600
	times['TotalSat2'] = sa2t.total_seconds()/3600
	times['TotalAll'] = (su1t+mo1t+tu1t+we1t+th1t+fr1t+sa1t+su2t+mo2t+tu2t+we2t+th2t+fr2t+sa2t).total_seconds()/3600
	start = find_closest_sunday(start_date)
	times['PeriodStart'] = start.strftime('%b %d')
	times['PeriodEnd'] = (start+timedelta(weeks=2,days=-1)).strftime('%b %d')
	name = "%s %s" % (employee.user.first_name, employee.user.last_name)
	times['Name'] = str(name)


	import os 
	folder = os.path.join(settings.MEDIA_ROOT,'files/temp')
	for the_file in os.listdir(folder):
	    file_path = os.path.join(folder, the_file)
	    try:
	        os.unlink(file_path)
	    except:
	        pass	
	f = open(os.path.join(settings.STATIC_ROOT, 'downloads/timesheet.html'), 'r')
	text = f.read()
	f.close()
	newText = Template(text).substitute(times)
	f2 = tempfile.NamedTemporaryFile(mode="w",suffix=".html",dir=os.path.join(settings.MEDIA_ROOT, "files/temp/"),delete=False) # open('populated_timesheet.html', 'w')
	f2.write(newText)
	return f2
