from django.contrib import admin
from .models import Task, TaskMember, ActivityLog

admin.site.register(Task)
admin.site.register(TaskMember)
admin.site.register(ActivityLog)
