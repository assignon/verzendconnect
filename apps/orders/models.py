import uuid
from decimal import Decimal
from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.core.models import Product, Costs


class Cart(models.Model):
    """Shopping cart for storing items before checkout."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Guest Cart ({self.session_key[:8]}...)"

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())

    @property
    def total(self):
        """Calculate total including BTW and delivery costs."""
        subtotal = self.subtotal
        costs = Costs.get_costs()
        
        # Calculate BTW based on type
        btw_amount = Decimal('0.00')
        if costs.btw_type == 'exclusif':
            # BTW is calculated on subtotal
            btw_amount = subtotal * (costs.btw_percentage / Decimal('100'))
        # If inclusif, BTW is already in prices, so we don't add it
        
        # Add delivery cost only if enabled
        delivery_cost = Decimal('0.00')
        if costs.delivery_cost_enabled:
            delivery_cost = costs.delivery_cost or Decimal('0.00')
        
        return subtotal + btw_amount + delivery_cost
    
    @property
    def btw_amount(self):
        """Calculate BTW amount based on settings."""
        costs = Costs.get_costs()
        if costs.btw_type == 'exclusif':
            return self.subtotal * (costs.btw_percentage / Decimal('100'))
        return Decimal('0.00')
    
    @property
    def delivery_cost(self):
        """Get delivery cost from settings if enabled."""
        costs = Costs.get_costs()
        if costs.delivery_cost_enabled:
            return costs.delivery_cost or Decimal('0.00')
        return Decimal('0.00')
    
    @property
    def delivery_cost_enabled(self):
        """Check if delivery cost is enabled."""
        costs = Costs.get_costs()
        return costs.delivery_cost_enabled

    def clear(self):
        self.items.all().delete()

    def merge_with(self, other_cart):
        """Merge another cart (guest cart) into this one."""
        for item in other_cart.items.all():
            existing = self.items.filter(product=item.product).first()
            if existing:
                existing.quantity += item.quantity
                existing.save()
            else:
                item.cart = self
                item.save()
        other_cart.delete()


class CartItem(models.Model):
    """Individual item in a shopping cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    # Rental dates
    rental_start_date = models.DateField(null=True, blank=True)
    rental_end_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product', 'rental_start_date', 'rental_end_date']
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def price(self):
        return self.product.current_price

    @property
    def total(self):
        return self.price * self.quantity

    @property
    def rental_days(self):
        """Calculate number of rental days."""
        if self.rental_start_date and self.rental_end_date:
            return (self.rental_end_date - self.rental_start_date).days
        return 0


class Order(models.Model):
    """Customer orders."""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    # Order identification
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Customer info
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    # Shipping address
    shipping_first_name = models.CharField(max_length=50)
    shipping_last_name = models.CharField(max_length=50)
    shipping_company = models.CharField(max_length=100, blank=True)
    shipping_address = models.CharField(max_length=200)
    shipping_address_2 = models.CharField(max_length=200, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='Netherlands')
    
    # Billing address (optional, can be same as shipping)
    billing_same_as_shipping = models.BooleanField(default=True)
    billing_first_name = models.CharField(max_length=50, blank=True)
    billing_last_name = models.CharField(max_length=50, blank=True)
    billing_company = models.CharField(max_length=100, blank=True)
    billing_address = models.CharField(max_length=200, blank=True)
    billing_address_2 = models.CharField(max_length=200, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)
    
    # Order details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Payment
    payment_method = models.CharField(max_length=50, blank=True)
    payment_id = models.CharField(max_length=100, blank=True)  # Mollie payment ID
    
    # Notes
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_order_number():
        """Generate a unique order number."""
        import random
        import string
        from datetime import datetime
        prefix = datetime.now().strftime('%Y%m')
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}-{suffix}"

    @property
    def shipping_full_name(self):
        return f"{self.shipping_first_name} {self.shipping_last_name}"

    @property
    def shipping_full_address(self):
        parts = [self.shipping_address]
        if self.shipping_address_2:
            parts.append(self.shipping_address_2)
        parts.append(f"{self.shipping_postal_code} {self.shipping_city}")
        if self.shipping_state:
            parts.append(self.shipping_state)
        parts.append(self.shipping_country)
        return ', '.join(parts)

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    """Individual item in an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)  # Saved in case product is deleted
    product_sku = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of rental
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Rental dates
    rental_start_date = models.DateField(null=True, blank=True)
    rental_end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)

    @property
    def rental_days(self):
        """Calculate number of rental days."""
        if self.rental_start_date and self.rental_end_date:
            return (self.rental_end_date - self.rental_start_date).days
        return 0

