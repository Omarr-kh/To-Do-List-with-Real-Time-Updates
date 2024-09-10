from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.models import User

from .serializers import ActivityLogSerializer, TaskSerializer
from .models import ActivityLog, Task, TaskMember
from .permissions import IsOwner

from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError, PermissionDenied

from fcm_django.models import FCMDevice


def send_notification_to_members(task, task_message):
    pass


class ViewLogs(generics.ListAPIView):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAdminUser]


@api_view(["POST"])
def register_user(request):
    if request.method == "POST":
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")

        if not username or not password or not email:
            return Response(
                {"error": "Username, Password and email are required!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists!!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create(username=username, email=email, password=password)
        Token.objects.create(user=user)

        return Response(
            {"message": "User registered successfully!"}, status=status.HTTP_201_CREATED
        )


@api_view(["POST"])
def login_user(request):
    if request.method == "POST":
        username = request.data.get("username")
        password = request.data.get("password")
        registration_token = request.data.get("registration_id")
        device_type = request.data.get("type")

        if not username or not password or not registration_token or not device_type:
            return Response(
                {
                    "error": "Username, Password, registration_id, and type are required!"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not User.objects.filter(username=username, password=password).exists():
            return Response(
                {"error": "Username or password are incorrect!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.get(username=username, password=password)
        token = Token.objects.get(user=user)

        if FCMDevice.objects.filter(registration_id=registration_token).exists():
            fcm_device = FCMDevice.objects.get(registration_id=registration_token)
            fcm_device.registration_id = registration_token
            fcm_device.type = device_type
            fcm_device.save()
        else:
            fcm_device = FCMDevice.objects.create(
                user=user, registration_id=registration_token, type=device_type
            )
        return Response({"token": {token.key}})


class ListCreateTask(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Get tasks where the user is either the owner or a member
        return Task.objects.filter(Q(owner=user) | Q(members__user=user)).distinct()

    def perform_create(self, serializer):
        task = serializer.save()
        members = self.request.data.get("members", [])
        if members:
            for username in members:
                try:
                    user = User.objects.get(username=username)
                    TaskMember.objects.create(task=task, user=user)
                except User.DoesNotExist:
                    raise ValidationError(f"user {username} doesn't exist")


class RetrieveUpdateDeleteTask(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def perform_update(self, serializer):
        task = self.get_object()
        user = self.request.user
        data = self.request.data

        if task.owner == user:
            serializer.save()

            if "status" in data:
                TaskMember.objects.filter(task=task).update(status=data["status"])

            members = self.request.data.get("members", [])
            if members:
                for username in members:
                    try:
                        user = User.objects.get(username=username)
                        if not TaskMember.objects.filter(task=task, user=user).exists():
                            TaskMember.objects.create(task=task, user=user)
                    except User.DoesNotExist:
                        raise ValidationError(f"user {username} doesn't exist")

            send_notification_to_members(task, "Task updated by owner.")
        else:
            task_member = TaskMember.objects.filter(task=task, user=user).first()
            task_member.status = data.get("status", task_member.status)
            task_member.save()
            send_notification_to_members(
                task, f"{user.username} updated their task status."
            )

    def perform_destroy(self, instance):
        send_notification_to_members(instance, "Task has been deleted by the creator.")
        super().perform_destroy(instance)
