from django import forms
from forum.models import *

class ThreadForm(forms.ModelForm):
        title = forms.CharField(max_length=60, required=True, label="Title")
        description = forms.CharField(max_length=5000, widget=forms.Textarea, label="Description")
        class Meta:
                model = Thread
                exclude = ('creator','created','forum','updated')

class PostForm(forms.ModelForm):
        title = forms.CharField(max_length=255, label="Title")
        body = forms.CharField(max_length=5000, widget=forms.Textarea, label="Body")
        class Meta:
                model = Post
                exclude = ('creator','updated','created','thread')
