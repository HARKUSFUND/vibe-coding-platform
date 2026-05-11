"""
Custom User model for bioplatform.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model using email as the unique identifier.
    """
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    # Additional fields
    phone = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    role = models.CharField(
        _('role'),
        max_length=50,
        choices=[
            ('admin', 'Administrateur'),
            ('technicien', 'Technicien'),
            ('biologiste', 'Biologiste'),
            ('medecin', 'Médecin'),
            ('operateur', 'Opérateur'),
        ],
        default='operateur'
    )
    laboratory = models.ForeignKey(
        'laboratoires.Laboratoire',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_login_at = models.DateTimeField(_('last login at'), null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['email']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the full name of the user."""
        return f'{self.first_name} {self.last_name}'.strip() or self.email
    
    def get_short_name(self):
        """Return the short name of the user."""
        return self.first_name or self.email
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_technician(self):
        return self.role == 'technicien'
    
    @property
    def is_biologist(self):
        return self.role == 'biologiste'
