"""
Custom permissions for User management.
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to admins
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users to edit their own profile or admins.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed to the user themselves or admins
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.id == obj.id)
        )


class IsTechnicianOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow technicians and admins to perform actions.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.is_technician
        )


class IsBiologistOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow biologists and admins to perform actions.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.is_biologist
        )
