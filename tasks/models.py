from django.db import models
from django.contrib.auth.models import User


STATUS_CHOICES = (
    ("Pending", "Pending"),
    ("Completed", "Completed"),
)


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    created_at = models.DateTimeField(auto_now_add=True)


class TaskMember(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="task_memberships"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")
