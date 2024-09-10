from django.shortcuts import render
from django.contrib.auth.models import User

from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from fcm_django.models import FCMDevice


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

        user = User.objects.create(
            username=username, email=email, password=password
        )
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
                {"error": "Username, Password, registration_id, and type are required!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not User.objects.filter(username=username, password=password).exists():
            return Response(
                {"error": "Username or password are incorrect!"},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = User.objects.get(username=username, password=password)
        token = Token.objects.get(user=user)

        if FCMDevice.objects.filter(registration_id=registration_token).exists():
            fcm_device = FCMDevice.objects.get(registration_id=registration_token)
            fcm_device["registration_id"] = registration_token
            fcm_device["type"] = device_type
            fcm_device.save()
        else:
            fcm_device = FCMDevice.objects.create(
                user=user, registration_id=registration_token, type=device_type
            )
        return Response({"token": {token.key}})
