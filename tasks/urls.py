from django.urls import path
from .views import register_user, login_user, ViewLogs

urlpatterns = [
    path("register/", register_user, name="register"),
    path("login/", login_user, name="login"),
    path("view-logs/", ViewLogs.as_view(), name="view-logs"),
]
