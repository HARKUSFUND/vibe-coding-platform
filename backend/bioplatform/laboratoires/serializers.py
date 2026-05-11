"""
Serializers for Laboratoires.
"""

from rest_framework import serializers
from .models import Laboratoire, Departement, Parametrage


class LaboratoireSerializer(serializers.ModelSerializer):
    """Serializer for Laboratoire model."""
    
    active_automates_count = serializers.IntegerField(read_only=True)
    pending_results_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Laboratoire
        fields = [
            'id', 'nom', 'code', 'adresse', 'ville', 'code_postal', 'pays',
            'telephone', 'email', 'site_web', 'timezone', 'langue', 'devise',
            'is_active', 'created_at', 'updated_at', 'active_automates_count',
            'pending_results_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DepartementSerializer(serializers.ModelSerializer):
    """Serializer for Departement model."""
    
    laboratoire_nom = serializers.CharField(source='laboratoire.nom', read_only=True)
    
    class Meta:
        model = Departement
        fields = [
            'id', 'laboratoire', 'laboratoire_nom', 'nom', 'code',
            'description', 'responsable', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ParametrageSerializer(serializers.ModelSerializer):
    """Serializer for Parametrage model."""
    
    laboratoire_nom = serializers.CharField(source='laboratoire.nom', read_only=True)
    
    class Meta:
        model = Parametrage
        fields = [
            'id', 'laboratoire', 'laboratoire_nom', 'cle', 'valeur',
            'type_valeur', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
