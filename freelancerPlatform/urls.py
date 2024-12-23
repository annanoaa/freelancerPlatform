from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import TemplateView

# API patterns
api_v1_patterns = [
    path('users/', include('users.urls')),
    path('projects/', include('projects.urls')),
    path('communications/', include('communications.urls')),
]

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Freelance Marketplace API",
        default_version='v1',
        description="API Documentation for Freelance Marketplace Platform",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[path('api/v1/', include(api_v1_patterns))],
)

# Main URL patterns
urlpatterns = [
    # Root URL - this should be first
    path('', TemplateView.as_view(template_name='index.html')),

    # Admin URL
    path('admin/', admin.site.urls),

    # API URLs
    path('api/v1/', include(api_v1_patterns)),

    # Swagger documentation URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

