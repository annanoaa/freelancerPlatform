from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.decorators.cache import never_cache

# First define your API patterns
api_v1_patterns = [
    path('api/v1/users/', include('users.urls')),
    path('api/v1/projects/', include('projects.urls')),
    path('api/v1/communications/', include('communications.urls')),
]

# Then create schema view
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
    permission_classes=[permissions.AllowAny,],
    patterns=api_v1_patterns,
)

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('admin/', admin.site.urls),

    # Include API patterns directly in urlpatterns
    *api_v1_patterns,

    # Swagger URLs - wrapped with never_cache
    path('swagger/', never_cache(schema_view.with_ui('swagger', cache_timeout=0)), name='schema-swagger-ui'),
    path('swagger.json', never_cache(schema_view.without_ui(cache_timeout=0)), name='schema-json'),
    path('redoc/', never_cache(schema_view.with_ui('redoc', cache_timeout=0)), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)