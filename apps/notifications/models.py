from django.db import models
from django.conf import settings


class EmailTemplate(models.Model):
    """Email templates for various notifications."""
    TEMPLATE_TYPE_CHOICES = [
        ('order_confirmation', 'Order Confirmation'),
        ('order_status_update', 'Order Status Update'),
        ('payment_received', 'Payment Received'),
        ('payment_failed', 'Payment Failed'),
        ('shipping_notification', 'Shipping Notification'),
        ('account_verification', 'Account Verification'),
        ('password_reset', 'Password Reset'),
        ('welcome', 'Welcome Email'),
        ('newsletter', 'Newsletter'),
    ]

    name = models.CharField(max_length=100)
    template_type = models.CharField(
        max_length=30, 
        choices=TEMPLATE_TYPE_CHOICES, 
        unique=True
    )
    subject = models.CharField(max_length=200)
    body_html = models.TextField(help_text="HTML email body. Use {{ variable }} for placeholders.")
    body_text = models.TextField(blank=True, help_text="Plain text email body (optional).")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'

    def __str__(self):
        return self.name


class Notification(models.Model):
    """In-app notifications for admin users."""
    NOTIFICATION_TYPE_CHOICES = [
        ('new_order', 'New Order'),
        ('payment_received', 'Payment Received'),
        ('low_stock', 'Low Stock Alert'),
        ('new_customer', 'New Customer'),
        ('order_cancelled', 'Order Cancelled'),
        ('refund_requested', 'Refund Requested'),
        ('system', 'System Notification'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True)  # URL to related object
    
    # Related objects (optional)
    related_order_id = models.PositiveIntegerField(null=True, blank=True)
    related_product_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.title} - {self.recipient.email}"

    def mark_as_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class EmailLog(models.Model):
    """Log of sent emails for tracking."""
    recipient = models.EmailField()
    subject = models.CharField(max_length=200)
    template = models.ForeignKey(
        EmailTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    status = models.CharField(max_length=20, default='sent')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'

    def __str__(self):
        return f"Email to {self.recipient}: {self.subject}"

