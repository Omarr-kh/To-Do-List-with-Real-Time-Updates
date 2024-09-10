from rest_framework import serializers
from .models import Task, TaskMember, ActivityLog
from django.contrib.auth.models import User


class TaskSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    members = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = Task
        fields = ["owner", "title", "description", "status", "members"]

    def get_owner(self, obj):
        return obj.owner.username

    def to_representation(self, instance):
        """Override the representation to include member usernames"""
        response = super().to_representation(instance)
        response["members"] = instance.members.values_list("user__username", flat=True)
        return response

    def create(self, validated_data):
        # Automatically assign the owner
        validated_data["owner"] = self.context["request"].user

        # Remove members from validated_data so it's not used by the parent 'create' method
        validated_data.pop("members", [])

        return super().create(validated_data)


class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = ["id", "username", "endpoint", "method", "timestamp"]

    def get_username(self, obj):
        return obj.user.username
