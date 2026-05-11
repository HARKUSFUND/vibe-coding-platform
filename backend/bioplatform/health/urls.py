"""
URLs for health check endpoints.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check, name='health_check'),
    path('ready/', views.readiness_check, name='readiness_check'),
    path('api/', views.HealthCheckView.as_view(), name='health_check_api'),
    path('detailed/', views.DetailedHealthCheckView.as_view(), name='health_check_detailed'),
]
