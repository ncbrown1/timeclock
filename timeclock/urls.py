from django.conf import settings
from django.conf.urls import patterns, include, url, RegexURLResolver
from django.contrib.auth.models import User
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.views import login, logout, password_change, password_change_done
from django.views.generic import TemplateView
from clock import views
from forum import views as fviews

from django.contrib import admin
admin.autodiscover()

def group(regex, *args):
	return RegexURLResolver(regex, args)

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.index, name='home'),
    (r'^login/', login, {'template_name': 'timeclock/login.html'}),
    url(r'login_success/', views.login_success, name="login_success"),
    (r'^logout/', logout, {'next_page': '/'}),
    (r'^password-change/', password_change, {'template_name': 'timeclock/passwordchange.html', 'post_change_redirect': '/password-change-success/'}),
    (r'^password-change-success/', TemplateView.as_view(template_name='timeclock/passwordchangesuccess.html')),
    url(r'^register/', views.register, name="register"),
    group(r'^profile/', 
	url(r'^$', views.profile, name="user-profile"),
	url(r'^clockevent-history/', views.clockevent_history, name="clockevent-history"),
    ),
    url(r'^superprofile/', views.superprofile, name="superprofile"),
    group(r'^super-clockevent-history/', 
	url(r'^$', views.super_clockevent_history, name="super-clockevent-history"),
	url(r'(\d+)/$', views.employee_history, name="employee-history")
    ),
    url(r'^edit-profile/', views.edit_profile, name="edit-profile"),
    group(r'^staff-forum/',
	url(r'^$', fviews.main_forum, name='main_forum'),
	url(r'^(\d+)/$', fviews.forum, name='forum-detail'),
	url(r'^thread/(\d+)/$', fviews.thread, name="thread-detail"),
	url(r'^reply/(\d+)/$', fviews.post_reply, name="reply"),
	url(r'^newthread/(\d+)/$', fviews.new_thread, name="new-thread"),
    ),
    url(r'^get-clocked-in-employees', views.json_in_employees, name="get-clocked-in-employees"),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT, 'show_indexes': True }),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True }),
)

urlpatterns += staticfiles_urlpatterns()
