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
from firebase_admin.messaging import MulticastMessage, Notification, send_multicast

import traceback


def send_notification_to_members(task, message_text):
    members = task.members.all()
    registration_ids = []

    for member in members:
        user = member.user
        try:
            # Get the FCM device token for the user
            fcm_device = FCMDevice.objects.get(user=user.id)
            registration_token = fcm_device.registration_id
            registration_ids.append(registration_token)
        except FCMDevice.DoesNotExist:
            continue

    if registration_ids:
        notification = Notification(title="Task Notification", body=message_text)

        message = MulticastMessage(
            notification=notification,
            tokens=registration_ids,
        )

        response = send_multicast(message)
        print(
            f"Successfully sent message: {response.success_count} messages sent, {response.failure_count} failed"
        )


@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def view_logs(request):
    try:
        logs = ActivityLog.objects.all()
        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data)
    except:
        print(traceback.format_exception)
        return Response(status=status.HTTP_409_CONFLICT)


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


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def list_tasks(request):
    try:
        user = request.user
        user_tasks = Task.objects.filter(Q(owner=user) | Q(members__user=user))
        serializer = TaskSerializer(user_tasks, many=True)

        return Response(serializer.data)
    except:
        print(traceback.format_exception)
        return Response(status=status.HTTP_409_CONFLICT)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_task(request):
    try:
        serializer = TaskSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            task = serializer.save()
            members = request.data.get("members", [])
            for username in members:
                try:
                    user = User.objects.get(username=username)
                    TaskMember.objects.create(user=user, task=task)
                except User.DoesNotExist:
                    raise ValidationError(f"{user} doesn't exist!")
        return Response(serializer.data)
    except:
        print(traceback.format_exception)
        return Response(status=status.HTTP_409_CONFLICT)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def view_task(request, pk):
    try:
        task = Task.objects.get(id=pk)
        if not (
            request.user == task.owner
            or task.members.filter(user=request.user).exists()
        ):
            raise PermissionDenied("You do not have permission to view this task.")

        serializer = TaskSerializer(task, many=False)
        return Response(serializer.data)
    except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=404)
    except:
        print(traceback.format_exception)
        return Response(status=status.HTTP_409_CONFLICT)


@api_view(["POST", "PUT"])
@permission_classes([permissions.IsAuthenticated])
def update_task(request, pk):
    try:
        task = Task.objects.get(id=pk)
        serializer = TaskSerializer(
            instance=task, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)
    except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=404)
    except:
        print(traceback.format_exception)
        return Response(status=status.HTTP_409_CONFLICT)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied


@api_view(["POST", "PUT"])
@permission_classes([permissions.IsAuthenticated])
def update_task(request, pk):
    try:
        task = Task.objects.get(id=pk)
        user = request.user
        data = request.data
        serializer = TaskSerializer(task, data=data, partial=True)

        if task.owner == user:
            if serializer.is_valid():
                serializer.save()

                # Update all members' status if the task status is updated by the owner
                if "status" in data:
                    TaskMember.objects.filter(task=task).update(status=data["status"])

                members = data.get("members", [])
                if members:
                    for username in members:
                        try:
                            member_user = User.objects.get(username=username)
                            if not TaskMember.objects.filter(
                                task=task, user=member_user
                            ).exists():
                                TaskMember.objects.create(task=task, user=member_user)
                        except User.DoesNotExist:
                            raise ValidationError(f"user {username} doesn't exist")

                send_notification_to_members(task, "Task updated by owner.")
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=400)
        else:
            # Members can update their task status
            task_member = TaskMember.objects.get(task=task, user=user)
            if task_member:
                task_member.status = data.get("status", task_member.status)
                task_member.save()
                send_notification_to_members(
                    task, f"{task_member.user} updated their task status."
                )
                return Response({"status": "Task status updated for member."})
            else:
                raise PermissionDenied(
                    "You do not have permission to update this task."
                )
    except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=404)
    except:
        print(traceback.format_exception)
        return Response(status=status.HTTP_409_CONFLICT)


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def delete_task(request, pk):
    try:
        task = Task.objects.get(id=pk)

        if request.user != task.owner:
            raise PermissionDenied(
                "You don't have permission to delete this task, only the owner can."
            )

        send_notification_to_members(task, "Task has been deleted by the creator.")
        task.delete()
        return Response({"message": "Task deleted successfully."})
    except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=404)
    except:
        print(traceback.format_exception)
        return Response(status=status.HTTP_409_CONFLICT)
