from rest_framework import serializers
from .models import Task, TaskMember, ActivityLog


class TaskSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["owner", "title", "description", "status"]

    def get_owner(self, obj):
        return obj.user.username
    
    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user.profile
        return super().create(validated_data)


class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = ["id", "username", "endpoint", "method", "timestamp"]

    def get_username(self, obj):
        return obj.user.username
