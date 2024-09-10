from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            return request.user == obj.owner
        else:
            return request.user == obj.owner or obj.members.filter(user=request.user).exists()


# class IsMember(permissions.BasePermission):
#     def has_object_permission(self, request, view, obj):
#         if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
#             return True

#         # Check if the request user is the owner of the task or a member
#         return (
#             request.user == obj.owner or obj.members.filter(user=request.user).exists()
#         )
