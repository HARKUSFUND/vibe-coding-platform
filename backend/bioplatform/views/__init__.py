"""
Views for bioplatform project.
"""

from django.shortcuts import render
from django.http import JsonResponse


def error_404(request, exception):
    """Custom 404 error handler."""
    return JsonResponse({
        'error': 'Not Found',
        'message': 'La ressource demandée n\'existe pas.',
        'status_code': 404
    }, status=404)


def error_500(request):
    """Custom 500 error handler."""
    return JsonResponse({
        'error': 'Internal Server Error',
        'message': 'Une erreur interne est survenue.',
        'status_code': 500
    }, status=500)
