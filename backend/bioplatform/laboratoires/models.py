"""
Models for Laboratoires.
Gestion des laboratoires et de leurs configurations.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Laboratoire(models.Model):
    """
    Modèle représentant un laboratoire d'analyses médicales.
    """
    nom = models.CharField(_('nom du laboratoire'), max_length=200)
    code = models.CharField(_('code'), max_length=50, unique=True)
    adresse = models.TextField(_('adresse'))
    ville = models.CharField(_('ville'), max_length=100)
    code_postal = models.CharField(_('code postal'), max_length=20)
    pays = models.CharField(_('pays'), max_length=100, default='France')
    telephone = models.CharField(_('téléphone'), max_length=20)
    email = models.EmailField(_('email'))
    site_web = models.URLField(_('site web'), blank=True, null=True)
    
    # Configuration
    timezone = models.CharField(_('fuseau horaire'), max_length=50, default='Europe/Paris')
    langue = models.CharField(_('langue'), max_length=10, default='fr')
    devise = models.CharField(_('devise'), max_length=3, default='EUR')
    
    # Statut
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('laboratoire')
        verbose_name_plural = _('laboratoires')
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
    
    @property
    def active_automates_count(self):
        """Return the number of active automates in this laboratory."""
        return self.automates.filter(is_active=True).count()
    
    @property
    def pending_results_count(self):
        """Return the number of pending results."""
        from bioplatform.resultats.models import Resultat
        return Resultat.objects.filter(
            automate__laboratoire=self,
            statut='pending'
        ).count()


class Departement(models.Model):
    """
    Département au sein d'un laboratoire (ex: Biochimie, Hématologie, etc.).
    """
    laboratoire = models.ForeignKey(
        Laboratoire,
        on_delete=models.CASCADE,
        related_name='departements'
    )
    nom = models.CharField(_('nom du département'), max_length=100)
    code = models.CharField(_('code'), max_length=20)
    description = models.TextField(_('description'), blank=True)
    responsable = models.CharField(_('responsable'), max_length=200, blank=True)
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('département')
        verbose_name_plural = _('départements')
        unique_together = [['laboratoire', 'code']]
        ordering = ['laboratoire', 'nom']
    
    def __str__(self):
        return f"{self.laboratoire.code} - {self.nom}"


class Parametrage(models.Model):
    """
    Paramètres de configuration du laboratoire.
    """
    laboratoire = models.ForeignKey(
        Laboratoire,
        on_delete=models.CASCADE,
        related_name='parametrages'
    )
    cle = models.CharField(_('clé'), max_length=100)
    valeur = models.TextField(_('valeur'))
    type_valeur = models.CharField(
        _('type'),
        max_length=20,
        choices=[
            ('string', 'Chaîne de caractères'),
            ('integer', 'Entier'),
            ('float', 'Nombre décimal'),
            ('boolean', 'Booléen'),
            ('json', 'JSON'),
        ],
        default='string'
    )
    description = models.TextField(_('description'), blank=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('paramétrage')
        verbose_name_plural = _('paramétrages')
        unique_together = [['laboratoire', 'cle']]
    
    def __str__(self):
        return f"{self.laboratoire.code} - {self.cle}"
