from rest_framework import permissions


class isOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == "GET":
            return True
        else:
            return request.user == obj.user
