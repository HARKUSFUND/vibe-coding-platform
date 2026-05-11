"""
Models for Résultats.
Gestion des résultats d'analyses médicales.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


class Analyse(models.Model):
    """
    Modèle représentant une analyse médicale en cours ou terminée.
    """
    STATUT_CHOICES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('validated', 'Validée'),
        ('cancelled', 'Annulée'),
        ('error', 'Erreur'),
    ]
    
    PRIORITE_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT'),
    ]
    
    # Identification
    laboratoire = models.ForeignKey(
        'laboratoires.Laboratoire',
        on_delete=models.CASCADE,
        related_name='analyses'
    )
    automate = models.ForeignKey(
        'automates.Automate',
        on_delete=models.CASCADE,
        related_name='analyses'
    )
    programme = models.ForeignKey(
        'automates.Programme',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analyses'
    )
    
    # Informations patient/échantillon
    patient_id = models.CharField(_('ID patient'), max_length=50, blank=True)
    patient_nom = models.CharField(_('nom patient'), max_length=100, blank=True)
    patient_prenom = models.CharField(_('prénom patient'), max_length=100, blank=True)
    patient_date_naissance = models.DateField(_('date naissance'), null=True, blank=True)
    patient_sexe = models.CharField(
        _('sexe'),
        max_length=10,
        choices=[('M', 'Masculin'), ('F', 'Féminin'), ('U', 'Non spécifié')],
        blank=True
    )
    
    echantillon_id = models.CharField(_('ID échantillon'), max_length=50, unique=True)
    echantillon_type = models.CharField(
        _('type échantillon'),
        max_length=50,
        choices=[
            ('sang', 'Sang'),
            ('serum', 'Sérum'),
            ('plasma', 'Plasma'),
            ('urine', 'Urine'),
            ('liquide_cephalo_rachidien', 'LCR'),
            ('salive', 'Salive'),
            ('autre', 'Autre'),
        ],
        default='sang'
    )
    
    # Suivi
    priorite = models.CharField(
        _('priorité'),
        max_length=20,
        choices=PRIORITE_CHOICES,
        default='routine'
    )
    statut = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='pending'
    )
    
    date_demande = models.DateTimeField(_('date demande'), auto_now_add=True)
    date_debut = models.DateTimeField(_('date début'), null=True, blank=True)
    date_fin = models.DateTimeField(_('date fin'), null=True, blank=True)
    date_validation = models.DateTimeField(_('date validation'), null=True, blank=True)
    
    # Résultat
    resultat_brut = models.TextField(_('résultat brut'), blank=True)
    resultat_formate = models.TextField(_('résultat formaté'), blank=True)
    unite = models.CharField(_('unité'), max_length=50, blank=True)
    valeur_numerique = models.DecimalField(
        _('valeur numérique'),
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True
    )
    valeur_min_reference = models.DecimalField(
        _('valeur min référence'),
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True
    )
    valeur_max_reference = models.DecimalField(
        _('valeur max référence'),
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True
    )
    drapeau = models.CharField(
        _('drapeau'),
        max_length=50,
        blank=True,
        help_text="Indicateurs: H (High), L (Low), HH (Very High), LL (Very Low)"
    )
    
    # Validation
    valide_par = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analyses_validees'
    )
    commentaires = models.TextField(_('commentaires'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('analyse')
        verbose_name_plural = _('analyses')
        ordering = ['-date_demande']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['echantillon_id']),
            models.Index(fields=['patient_id']),
            models.Index(fields=['date_demande']),
        ]
    
    def __str__(self):
        return f"{self.echantillon_id} - {self.statut}"
    
    @property
    def duree_execution(self):
        """Return execution duration in seconds."""
        if self.date_debut and self.date_fin:
            return (self.date_fin - self.date_debut).total_seconds()
        return None
    
    @property
    def is_normal(self):
        """Check if result is within reference range."""
        if self.valeur_numerique is None:
            return None
        if self.valeur_min_reference and self.valeur_numerique < self.valeur_min_reference:
            return False
        if self.valeur_max_reference and self.valeur_numerique > self.valeur_max_reference:
            return False
        return True
    
    @property
    def should_be_validated(self):
        """Check if analysis is ready for validation."""
        return self.statut == 'completed' and self.resultat_formate != ''


class Resultat(models.Model):
    """
    Modèle pour stocker les résultats finaux validés.
    """
    analyse = models.OneToOneField(
        Analyse,
        on_delete=models.CASCADE,
        related_name='resultat'
    )
    
    # Copie des données pour archivage
    patient_id = models.CharField(_('ID patient'), max_length=50)
    echantillon_id = models.CharField(_('ID échantillon'), max_length=50)
    test_code = models.CharField(_('code test'), max_length=50)
    test_nom = models.CharField(_('nom test'), max_length=200)
    resultat_valeur = models.TextField(_('valeur'))
    unite = models.CharField(_('unité'), max_length=50, blank=True)
    valeurs_reference = models.TextField(_('valeurs de référence'), blank=True)
    drapeaux = models.CharField(_('drapeaux'), max_length=100, blank=True)
    
    # Métadonnées ASTM/HL7
    message_astm = models.TextField(_('message ASTM'), blank=True)
    checksum = models.CharField(_('checksum'), max_length=10, blank=True)
    
    date_creation = models.DateTimeField(_('date création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('résultat')
        verbose_name_plural = _('résultats')
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.echantillon_id} - {self.test_code}"


class HistoriqueStatut(models.Model):
    """
    Historique des changements de statut des analyses.
    """
    analyse = models.ForeignKey(
        Analyse,
        on_delete=models.CASCADE,
        related_name='historique_statuts'
    )
    ancien_statut = models.CharField(_('ancien statut'), max_length=20)
    nouveau_statut = models.CharField(_('nouveau statut'), max_length=20)
    commentaire = models.TextField(_('commentaire'), blank=True)
    utilisateur = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('historique statut')
        verbose_name_plural = _('historiques statuts')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.analyse.echantillon_id}: {self.ancien_statut} → {self.nouveau_statut}"
