"""
URL Configuration for bioplatform project.
Plateforme biomédicale interconnectée
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API Schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="BioPlatform API",
        default_version='v1',
        description="API pour la plateforme biomédicale interconnectée - Gestion des automates et laboratoires",
        terms_of_service="https://www.bioplatform.com/terms/",
        contact=openapi.Contact(email="contact@bioplatform.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # API v1 endpoints
    path('api/v1/auth/', include('rest_framework_simplejwt.urls')),
    path('api/v1/users/', include('bioplatform.users.urls')),
    path('api/v1/automates/', include('bioplatform.automates.urls')),
    path('api/v1/laboratoires/', include('bioplatform.laboratoires.urls')),
    path('api/v1/resultats/', include('bioplatform.resultats.urls')),
    path('api/v1/astm/', include('bioplatform.astm_connector.urls')),
    
    # Health check
    path('health/', include('bioplatform.health.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error pages
handler404 = 'bioplatform.views.error_404'
handler500 = 'bioplatform.views.error_500'
