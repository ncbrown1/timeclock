from django.contrib import admin
from forum.models import *

class ForumAdmin(admin.ModelAdmin):
        pass

class ThreadAdmin(admin.ModelAdmin):
        list_display = ['title', 'forum', 'creator', 'created']
        lsit_filter = ['forum', 'creator']

class PostAdmin(admin.ModelAdmin):
        list_display = ['title', 'thread', 'creator', 'created']
        list_filter = ['created', 'creator']
        search_fields = ['title', 'creator']
        date_hierarchy = 'created'
        save_on_top = True

admin.site.register(Forum, ForumAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(Post, PostAdmin)
