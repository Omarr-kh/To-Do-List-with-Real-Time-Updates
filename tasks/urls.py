from django.urls import path
from .views import (
    register_user,
    login_user,
    view_logs,
    list_tasks,
    view_task,
    create_task,
    update_task,
    delete_task,
)

urlpatterns = [
    path("register/", register_user, name="register"),
    path("login/", login_user, name="login"),
    path("view-logs/", view_logs, name="view-logs"),
    path("tasks/", list_tasks, name="list-tasks"),
    path("create-task/", create_task, name="create-task"),
    path("view-task/<int:pk>/", view_task, name="view-task"),
    path("update-task/<int:pk>/", update_task, name="update-task"),
    path("delete-task/<int:pk>/", delete_task, name="delete-task"),
]
