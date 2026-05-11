"""
Models for Automates.
Gestion des automates d'analyses médicales et leur connectivité.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Automate(models.Model):
    """
    Modèle représentant un automate d'analyses médicales.
    """
    laboratoire = models.ForeignKey(
        'laboratoires.Laboratoire',
        on_delete=models.CASCADE,
        related_name='automates'
    )
    nom = models.CharField(_('nom de l\'automate'), max_length=200)
    code = models.CharField(_('code'), max_length=50)
    modele = models.CharField(_('modèle'), max_length=100)
    fabricant = models.CharField(_('fabricant'), max_length=100)
    numero_serie = models.CharField(_('numéro de série'), max_length=100, unique=True)
    
    # Connectivité
    adresse_ip = models.GenericIPAddressField(_('adresse IP'), null=True, blank=True)
    port_communication = models.IntegerField(_('port'), default=8080)
    protocole = models.CharField(
        _('protocole'),
        max_length=20,
        choices=[
            ('astm', 'ASTM E1381/E1394'),
            ('hl7', 'HL7 v2.x'),
            ('rs232', 'RS-232'),
            ('tcp', 'TCP/IP'),
            ('udp', 'UDP'),
        ],
        default='astm'
    )
    
    # Statut
    is_active = models.BooleanField(_('actif'), default=True)
    is_connected = models.BooleanField(_('connecté'), default=False)
    last_connection = models.DateTimeField(_('dernière connexion'), null=True, blank=True)
    
    # Configuration
    intervalle_polling = models.IntegerField(
        _('intervalle de polling (secondes)'),
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(3600)]
    )
    timeout_communication = models.IntegerField(
        _('timeout (secondes)'),
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(300)]
    )
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('automate')
        verbose_name_plural = _('automates')
        unique_together = [['laboratoire', 'code']]
        ordering = ['laboratoire', 'nom']
    
    def __str__(self):
        return f"{self.laboratoire.code} - {self.nom}"
    
    @property
    def status_display(self):
        """Return human-readable status."""
        if not self.is_active:
            return 'Inactif'
        elif self.is_connected:
            return 'Connecté'
        else:
            return 'Déconnecté'
    
    @property
    def pending_analyses_count(self):
        """Return the number of pending analyses for this automate."""
        from bioplatform.resultats.models import Analyse
        return Analyse.objects.filter(
            automate=self,
            statut='pending'
        ).count()


class Programme(models.Model):
    """
    Programme d'analyse sur un automate.
    """
    automate = models.ForeignKey(
        Automate,
        on_delete=models.CASCADE,
        related_name='programmes'
    )
    nom = models.CharField(_('nom du programme'), max_length=100)
    code = models.CharField(_('code'), max_length=50)
    description = models.TextField(_('description'), blank=True)
    duree_estimee = models.IntegerField(
        _('durée estimée (minutes)'),
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('programme')
        verbose_name_plural = _('programmes')
        unique_together = [['automate', 'code']]
        ordering = ['automate', 'nom']
    
    def __str__(self):
        return f"{self.automate.code} - {self.nom}"


class Maintenance(models.Model):
    """
    Suivi des maintenances des automates.
    """
    TYPE_CHOICES = [
        ('preventive', 'Préventive'),
        ('corrective', 'Corrective'),
        ('calibration', 'Calibration'),
        ('verification', 'Vérification'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
    ]
    
    automate = models.ForeignKey(
        Automate,
        on_delete=models.CASCADE,
        related_name='maintenances'
    )
    type_maintenance = models.CharField(
        _('type'),
        max_length=20,
        choices=TYPE_CHOICES
    )
    description = models.TextField(_('description'))
    date_prevue = models.DateTimeField(_('date prévue'))
    date_debut = models.DateTimeField(_('date de début'), null=True, blank=True)
    date_fin = models.DateTimeField(_('date de fin'), null=True, blank=True)
    statut = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned'
    )
    technicien = models.CharField(_('technicien'), max_length=200, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('maintenance')
        verbose_name_plural = _('maintenances')
        ordering = ['-date_prevue']
    
    def __str__(self):
        return f"{self.automate.code} - {self.get_type_maintenance_display()} - {self.date_prevue.strftime('%Y-%m-%d')}"
