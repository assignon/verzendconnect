"""
URL configuration for VerzendConnect project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# Language switching
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

# URL patterns with language prefix
urlpatterns += i18n_patterns(
    path('admin/dashboard/', include('apps.dashboard.urls')),
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('cart/', include('apps.orders.urls')),
    path('payments/', include('apps.payments.urls')),
    path('api/', include('apps.core.api_urls')),
    prefix_default_language=False,  # Don't prefix default language (Dutch)
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar - Temporarily disabled
    # import debug_toolbar
    # urlpatterns = [
    #     path('__debug__/', include(debug_toolbar.urls)),
    # ] + urlpatterns

