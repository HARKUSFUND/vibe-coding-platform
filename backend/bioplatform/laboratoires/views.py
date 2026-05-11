"""
Views for Laboratoires management.
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Laboratoire, Departement, Parametrage
from .serializers import LaboratoireSerializer, DepartementSerializer, ParametrageSerializer


class LaboratoireViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing laboratories.
    """
    queryset = Laboratoire.objects.all()
    serializer_class = LaboratoireSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'pays', 'ville']
    search_fields = ['nom', 'code', 'email', 'telephone']
    ordering_fields = ['nom', 'created_at', 'ville']
    ordering = ['nom']
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        """Get statistics for a laboratory."""
        laboratoire = self.get_object()
        stats = {
            'laboratoire': laboratoire.nom,
            'total_automates': laboratoire.automates.count(),
            'automates_actifs': laboratoire.active_automates_count,
            'analyses_en_attente': laboratoire.pending_results_count,
            'total_departements': laboratoire.departements.count(),
        }
        return Response(stats)


class DepartementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing departments.
    """
    queryset = Departement.objects.all()
    serializer_class = DepartementSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['laboratoire', 'is_active']
    search_fields = ['nom', 'code', 'responsable']
    ordering_fields = ['nom', 'created_at']
    ordering = ['laboratoire', 'nom']
    permission_classes = [permissions.IsAuthenticated]


class ParametrageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing laboratory settings.
    """
    queryset = Parametrage.objects.all()
    serializer_class = ParametrageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['laboratoire', 'type_valeur']
    search_fields = ['cle', 'description']
    ordering_fields = ['cle', 'created_at']
    ordering = ['laboratoire', 'cle']
    permission_classes = [permissions.IsAuthenticated]
