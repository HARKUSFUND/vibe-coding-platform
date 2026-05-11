"""
Views for User management.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .serializers import UserSerializer, UserCreateSerializer
from .permissions import IsAdminOrReadOnly, IsSelfOrAdmin

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.
    
    list: Return all users.
    create: Create a new user.
    retrieve: Return a specific user.
    update: Update a user.
    destroy: Delete a user.
    """
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'is_active', 'laboratory']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering_fields = ['email', 'created_at', 'last_login_at']
    ordering = ['email']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['retrieve', 'me']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        if user.is_admin:
            return User.objects.all()
        # Non-admin users can only see themselves
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current authenticated user."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """Register a new user."""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def activate(self, request, pk=None):
        """Activate a user account."""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'user activated'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def deactivate(self, request, pk=None):
        """Deactivate a user account."""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'user deactivated'})
