from rest_framework import permissions

from projects.models import ProjectBid


class IsProjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.client == request.user


class IsProjectParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (obj.client == request.user or
                obj.freelancer == request.user or
                obj.bids.filter(freelancer=request.user).exists())


class CanSubmitBid(permissions.BasePermission):
    message = "Only freelancers can submit bids on projects."

    def has_permission(self, request, view):
        # Check if user is authenticated and is a freelancer
        return request.user.is_authenticated and request.user.role == 'FR'

    def has_object_permission(self, request, view, obj):
        # For GET requests and bid withdrawal
        if request.method in permissions.SAFE_METHODS or view.action == 'withdraw_bid':
            if isinstance(obj, ProjectBid):
                return obj.freelancer == request.user
            return True

        return True


class CanManageMilestones(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Only project owner can create/update milestones
        if request.method in ['POST', 'PUT', 'PATCH']:
            return obj.client == request.user
        # Both client and freelancer can view milestones
        return obj.client == request.user or obj.freelancer == request.user