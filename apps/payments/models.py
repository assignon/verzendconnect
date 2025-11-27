from django.db import models
from django.conf import settings
from apps.orders.models import Order


class Payment(models.Model):
    """Payment records for orders."""
    PAYMENT_METHOD_CHOICES = [
        ('ideal', 'iDEAL'),
        ('paypal', 'PayPal'),
        ('creditcard', 'Credit Card'),
        ('banktransfer', 'Bank Transfer'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('authorized', 'Authorized'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    
    # Mollie payment details
    mollie_payment_id = models.CharField(max_length=100, unique=True)
    mollie_checkout_url = models.URLField(blank=True)
    
    # Payment info
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Metadata
    description = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment {self.mollie_payment_id} for Order #{self.order.order_number}"


class Refund(models.Model):
    """Refund records for payments."""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    mollie_refund_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'

    def __str__(self):
        return f"Refund {self.mollie_refund_id}"

