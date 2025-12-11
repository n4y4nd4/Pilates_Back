#!/usr/bin/env python
"""Script para listar todos os URLs disponíveis na API"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pilates_cobranca.settings")
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def show_urls(urlpatterns, prefix=''):
    """Recursivamente mostrar todos os URLs"""
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            show_urls(pattern.url_patterns, prefix + str(pattern.pattern))
        elif isinstance(pattern, URLPattern):
            print(f"{prefix}{pattern.pattern}")

# Obter resolver
resolver = get_resolver()

print("=" * 60)
print("URLS DISPONÍVEIS NA API")
print("=" * 60)
show_urls(resolver.url_patterns)
print("=" * 60)
