from .models import SiteSettings, Category, EventType


def site_settings(request):
    """Add site settings and navigation data to all templates."""
    settings = SiteSettings.get_settings()
    categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('subcategories')
    event_types = EventType.objects.filter(is_active=True)
    
    return {
        'site_settings': settings,
        'nav_categories': categories,
        'nav_event_types': event_types,
    }

