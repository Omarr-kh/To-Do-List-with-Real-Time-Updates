from django.contrib import admin
from .models import Task, TaskMember

admin.site.register(Task)
admin.site.register(TaskMember)
