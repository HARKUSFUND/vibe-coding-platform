"""
Health check endpoints for monitoring and load balancers.
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'bioplatform'
    })


def readiness_check(request):
    """Readiness check - verifies all dependencies are available."""
    checks = {
        'database': False,
        'cache': False,
        'ready': False
    }
    
    # Check database
    try:
        connection.ensure_connection()
        checks['database'] = True
    except Exception as e:
        checks['database_error'] = str(e)
    
    # Check cache (Redis)
    try:
        cache.set('health_check', 'ok', timeout=10)
        result = cache.get('health_check')
        checks['cache'] = (result == 'ok')
    except Exception as e:
        checks['cache_error'] = str(e)
    
    # System is ready if all checks pass
    checks['ready'] = checks['database'] and checks['cache']
    
    http_status = status.HTTP_200_OK if checks['ready'] else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JsonResponse(checks, status=http_status)


class HealthCheckView(APIView):
    """DRF-based health check endpoint."""
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'bioplatform-api',
            'version': '1.0.0'
        })


class DetailedHealthCheckView(APIView):
    """Detailed health check with dependency verification."""
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'service': 'bioplatform-api',
            'version': '1.0.0',
            'checks': {}
        }
        
        overall_healthy = True
        
        # Database check
        try:
            connection.ensure_connection()
            health_status['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
            overall_healthy = False
        
        # Redis cache check
        try:
            cache.set('health_check', 'ok', timeout=10)
            result = cache.get('health_check')
            if result == 'ok':
                health_status['checks']['cache'] = {
                    'status': 'healthy',
                    'message': 'Redis cache connection successful'
                }
            else:
                raise Exception("Cache read/write mismatch")
        except Exception as e:
            health_status['checks']['cache'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
            overall_healthy = False
        
        if not overall_healthy:
            health_status['status'] = 'unhealthy'
        
        http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_status, status=http_status)
