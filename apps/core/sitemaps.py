"""
Sitemap configuration for VerzendConnect.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category, EventType


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages."""
    priority = 1.0
    changefreq = 'monthly'

    def items(self):
        return [
            'core:home',
            'core:about',
            'core:faq',
            'core:rental_terms',
            'core:product_list',
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    """Sitemap for products."""
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True).select_related('category')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    """Sitemap for categories."""
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class EventTypeSitemap(Sitemap):
    """Sitemap for event types."""
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return EventType.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()

