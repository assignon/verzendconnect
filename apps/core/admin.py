from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from .models import EventType, Category, Product, ProductImage, SiteSettings


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']


@admin.register(EventType)
class EventTypeAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'order', 'product_count']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active', 'is_featured', 'order', 'product_count']
    list_filter = ['is_active', 'is_featured', 'event_types']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['event_types']
    ordering = ['order', 'name']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name', 'category', 'price_display', 'stock', 'is_available', 'is_active', 'is_featured']
    list_filter = ['is_active', 'is_available', 'is_featured', 'category', 'event_types']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['event_types']
    inlines = [ProductImageInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'event_types')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Inventory', {
            'fields': ('stock', 'is_available', 'is_active', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        if obj.sale_price:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">€{}</span> '
                '<span style="color: #22c55e; font-weight: bold;">€{}</span>',
                obj.price, obj.sale_price
            )
        return f'€{obj.price}'
    price_display.short_description = 'Price'


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_tagline', 'logo', 'favicon')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'instagram_url', 'twitter_url'),
            'classes': ('collapse',)
        }),
        ('Business Settings', {
            'fields': ('currency', 'currency_symbol')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Footer', {
            'fields': ('footer_text',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance of SiteSettings
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

