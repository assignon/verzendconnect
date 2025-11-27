from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import EmailTemplate, Notification, EmailLog


@admin.register(EmailTemplate)
class EmailTemplateAdmin(ModelAdmin):
    list_display = ['name', 'template_type', 'subject', 'is_active', 'updated_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__email']
    readonly_fields = ['created_at', 'read_at']


@admin.register(EmailLog)
class EmailLogAdmin(ModelAdmin):
    list_display = ['recipient', 'subject', 'template', 'status', 'created_at']
    list_filter = ['status', 'template', 'created_at']
    search_fields = ['recipient', 'subject']
    readonly_fields = ['created_at']

