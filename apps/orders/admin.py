from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'total']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'quantity', 'price', 'total']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key_display', 'items_count', 'total_display', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'session_key']
    inlines = [CartItemInline]
    readonly_fields = ['created_at', 'updated_at']

    def session_key_display(self, obj):
        if obj.session_key:
            return f"{obj.session_key[:8]}..."
        return "-"
    session_key_display.short_description = 'Session'

    def total_display(self, obj):
        return f"€{obj.total:.2f}"
    total_display.short_description = 'Total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'email', 'total_display', 'status_badge', 'payment_status_badge', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'email', 'shipping_first_name', 'shipping_last_name']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'paid_at', 'shipped_at', 'completed_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'status', 'payment_status', 'payment_method', 'payment_id')
        }),
        ('Customer', {
            'fields': ('user', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': (
                ('shipping_first_name', 'shipping_last_name'),
                'shipping_company',
                'shipping_address',
                'shipping_address_2',
                ('shipping_city', 'shipping_postal_code'),
                ('shipping_state', 'shipping_country'),
            )
        }),
        ('Billing Address', {
            'fields': (
                'billing_same_as_shipping',
                ('billing_first_name', 'billing_last_name'),
                'billing_company',
                'billing_address',
                'billing_address_2',
                ('billing_city', 'billing_postal_code'),
                ('billing_state', 'billing_country'),
            ),
            'classes': ('collapse',)
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'discount', 'total')
        }),
        ('Notes', {
            'fields': ('customer_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'shipped_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def total_display(self, obj):
        return f"€{obj.total:.2f}"
    total_display.short_description = 'Total'

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'paid': '#3b82f6',
            'confirmed': '#8b5cf6',
            'preparing': '#6366f1',
            'shipped': '#0ea5e9',
            'delivered': '#22c55e',
            'completed': '#16a34a',
            'cancelled': '#ef4444',
            'refunded': '#f97316',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def payment_status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'processing': '#3b82f6',
            'paid': '#22c55e',
            'failed': '#ef4444',
            'refunded': '#f97316',
            'cancelled': '#6b7280',
        }
        color = colors.get(obj.payment_status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment'

