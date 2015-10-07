from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from clock.controllers import *
from clock.models import Employee
from forum.models import *
from forum.forms import *

signature = "\n\nThis message was sent via the Helpdesk Timeclock Internal Forum. If you would like to reply to this message,\
	 please	go to the forum and submit your reply there. https://localhost:8000/staff-forum/"

@login_required
@user_passes_test(is_employee, login_url='/login/')
def main_forum(request):
        forums = Forum.objects.all()
        return render_to_response('forum/list.html', {'forums': forums, 'user': request.user}, context_instance=RequestContext(request))

def mk_paginator(request, items, num_items):
        paginator = Paginator(items, num_items)
        try: page = int(request.GET.get("page", '1'))
        except ValueError: page = 1

        try: items = paginator.page(page)
        except (InvalidPage, EmptyPage): items = paginator.page(paginator.num_pages)
        return items

@login_required
@user_passes_test(is_employee, login_url='/login/')
def forum(request, forum_id):
        threads = Thread.objects.filter(forum=forum_id).order_by('-created')
        threads = mk_paginator(request, threads, 15)
        return render_to_response('forum/forum.html', {'threads': threads, 'pk': forum_id, 'user': request.user}, context_instance=RequestContext(request))

@login_required
@user_passes_test(is_employee, login_url='/login/')
def thread(request, thread_id):
        posts = Post.objects.filter(thread=thread_id).order_by("created")
        posts = mk_paginator(request, posts, 15)
        t = Thread.objects.get(pk=thread_id)
        return render_to_response('forum/thread.html', {'posts': posts, 'pk': thread_id, 'title': t.title, 'forum_pk': t.forum.pk, 'user': request.user}, context_instance=RequestContext(request))

@login_required
@user_passes_test(is_employee, login_url='/login/')
def post_reply(request, thread_id):
        form = PostForm()
        thread = Thread.objects.get(pk=thread_id)

        if request.method == 'POST':
                form = PostForm(request.POST)
                if form.is_valid():
                        post = Post()
                        post.thread = thread
                        post.title = form.cleaned_data['title']
                        post.body = form.cleaned_data['body']
                        post.creator = request.user
                        post.save()
                        return HttpResponseRedirect(reverse('thread-detail', args=(thread_id,)))
	else:
		post = Post()
		post.title = 'RE: %s' % thread.title
		form = PostForm(instance=post)
        return render_to_response('forum/reply.html', {'form':form, 'thread':thread,}, context_instance=RequestContext(request))

@login_required
@user_passes_test(is_employee, login_url='/login/')
def new_thread(request, forum_id):
        form = ThreadForm()
        forum = get_object_or_404(Forum, pk=forum_id)
        if request.method == 'POST':
                form = ThreadForm(request.POST)
                if form.is_valid():
                        thread = Thread()
                        thread.title = form.cleaned_data['title']
                        thread.description = form.cleaned_data['description']
                        thread.forum = forum
                        thread.creator = request.user
                        thread.save()
			post = Post()
			post.thread = thread
			post.title = thread.title
			post.body = thread.description
			post.creator = request.user
			post.save()
                        if forum.title == 'Announcements':
                                employees = Employee.objects.filter(user__groups__name='Help Desk Staff')
                                rcpts = []
                                for emp in employees:
                                        rcpts.append(emp.user.email)
                                send_mail('[Help Desk Announcement] ' + thread.title, thread.description + signature, 'no-reply@helpdesk.engr.ucsb.edu', rcpts, fail_silently=False)
                        return HttpResponseRedirect(reverse('forum-detail', args=(forum_id, )))
        return render_to_response('forum/new-topic.html', {'form':form, 'forum':forum, }, context_instance=RequestContext(request))
