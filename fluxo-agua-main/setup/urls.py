from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
import os

schema_view = get_schema_view(
    openapi.Info(
        title="API de Controle de Fluxo de Água",
        default_version='v1',
        description="""
        API para monitoramento e controle do fluxo de água em residências.

        ## Funcionalidades principais:
        - **Sensores**: Gerenciamento de sensores de água
        - **Fluxo de Água**: Registro de leituras dos sensores
        - **Meta de Consumo**: Configuração de meta diária de consumo
        - **Controle de Fluxo**: Monitoramento e controle automático/manual do fluxo (on/off)
        - **Consumo**: Consulta de consumo diário e mensal

        ## Base URL
        - Produção: https://fluxo-agua.kauan.space
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contato@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('fluxo.urls')),

    # Swagger/OpenAPI documentation
    re_path(r'^docs/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('docs/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('docs/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
