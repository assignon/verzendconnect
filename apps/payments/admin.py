from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from .models import Payment, Refund


class RefundInline(TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ['mollie_refund_id', 'amount', 'status', 'created_at', 'processed_at']


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ['mollie_payment_id', 'order_link', 'method', 'amount_display', 'status_badge', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['mollie_payment_id', 'order__order_number', 'order__email']
    readonly_fields = ['mollie_payment_id', 'mollie_checkout_url', 'created_at', 'updated_at', 'paid_at']
    inlines = [RefundInline]

    def order_link(self, obj):
        return format_html(
            '<a href="/admin/orders/order/{}/change/">{}</a>',
            obj.order.id, obj.order.order_number
        )
    order_link.short_description = 'Order'

    def amount_display(self, obj):
        return f"€{obj.amount:.2f}"
    amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        colors = {
            'open': '#f59e0b',
            'pending': '#f59e0b',
            'authorized': '#3b82f6',
            'paid': '#22c55e',
            'failed': '#ef4444',
            'expired': '#6b7280',
            'canceled': '#6b7280',
            'refunded': '#f97316',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Refund)
class RefundAdmin(ModelAdmin):
    list_display = ['mollie_refund_id', 'payment', 'amount_display', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['mollie_refund_id', 'payment__mollie_payment_id']
    readonly_fields = ['mollie_refund_id', 'created_at', 'processed_at']

    def amount_display(self, obj):
        return f"€{obj.amount:.2f}"
    amount_display.short_description = 'Amount'

