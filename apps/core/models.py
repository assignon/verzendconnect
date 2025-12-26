from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class EventType(models.Model):
    """Event types like Wedding, Birthday, Corporate, etc."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Material icon name")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='event_types/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Event Type'
        verbose_name_plural = 'Event Types'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('core:event_type_detail', kwargs={'slug': self.slug})


class Category(models.Model):
    """Product categories like Cakes, Decorations, Catering, DJs, etc."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    event_types = models.ManyToManyField(EventType, related_name='categories', blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('core:category_detail', kwargs={'slug': self.slug})

    @property
    def active_products(self):
        return self.products.filter(is_active=True)


class Product(models.Model):
    """Products and services for events."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products'
    )
    event_types = models.ManyToManyField(EventType, related_name='products', blank=True)
    
    # Inventory
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Rental Date Restrictions (optional - if set, clients can only rent within this range)
    rental_start_date = models.DateField(
        null=True, 
        blank=True, 
        help_text="Earliest date this product can be rented from. Leave empty for no restriction."
    )
    rental_end_date = models.DateField(
        null=True, 
        blank=True, 
        help_text="Latest date this product can be returned. Leave empty for no restriction."
    )
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.short_description and self.description:
            self.short_description = self.description[:297] + '...' if len(self.description) > 300 else self.description
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('core:product_detail', kwargs={'slug': self.slug})

    @property
    def primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        return primary if primary else self.images.first()

    @property
    def current_price(self):
        """Returns sale price if available, otherwise regular price."""
        return self.sale_price if self.sale_price else self.price

    @property
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return int(((self.price - self.sale_price) / self.price) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0 and self.is_available

    def get_min_rental_date(self):
        """Get the minimum date from which this product can be rented."""
        min_days = getattr(settings, 'MIN_BEGIN_DATE', 2)
        min_date = timezone.now().date() + timedelta(days=min_days)
        
        # If product has a rental_start_date restriction, use the later date
        if self.rental_start_date and self.rental_start_date > min_date:
            return self.rental_start_date
        return min_date

    def get_max_rental_date(self):
        """Get the maximum date until which this product can be rented."""
        return self.rental_end_date  # Returns None if no restriction

    def get_available_stock(self, start_date, end_date):
        """
        Calculate available stock for a given date range.
        Since stock is deducted immediately when order is placed,
        available stock = current stock + items returning before start_date
        """
        from apps.core.models import RentalRecord
        
        # Start with current stock (already has rentals deducted)
        available = self.stock
        
        # Add back items that will be returned BEFORE our rental starts
        # These items will be available by the time our rental begins
        returning_before_start = RentalRecord.objects.filter(
            product=self,
            is_returned=False,
            return_date__lt=start_date  # Return date is before our start
        )
        
        for rental in returning_before_start:
            available += rental.quantity
        
        return max(0, available)

    def can_rent(self, start_date, end_date, quantity):
        """Check if the product can be rented for the given dates and quantity."""
        # Check date restrictions
        min_date = self.get_min_rental_date()
        if start_date < min_date:
            return False, f"Rental cannot start before {min_date.strftime('%d-%m-%Y')}"
        
        max_date = self.get_max_rental_date()
        if max_date and end_date > max_date:
            return False, f"Rental cannot extend beyond {max_date.strftime('%d-%m-%Y')}"
        
        if end_date <= start_date:
            return False, "Return date must be after start date"
        
        # Check stock availability
        # Stock is now directly deducted when order is placed, so we check current stock
        # But for future rentals, we also count items that will be returned before start_date
        available = self.get_available_stock(start_date, end_date)
        if quantity > available:
            return False, f"Only {available} items available for this period"
        
        return True, "Available"


class RentalRecord(models.Model):
    """Track all product rentals for stock management."""
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='rental_records'
    )
    order_item = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.CASCADE,
        related_name='rental_record',
        null=True,
        blank=True
    )
    
    # Customer info
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rental_records'
    )
    customer_name = models.CharField(max_length=200, blank=True)
    customer_email = models.EmailField(blank=True)
    
    # Rental details
    quantity = models.PositiveIntegerField(default=1)
    rental_start_date = models.DateField()
    return_date = models.DateField()
    
    # Status
    is_returned = models.BooleanField(default=False)
    returned_at = models.DateTimeField(null=True, blank=True)
    overdue_notification_sent = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-rental_start_date', '-created_at']
        verbose_name = 'Rental Record'
        verbose_name_plural = 'Rental Records'

    def __str__(self):
        return f"{self.product.name} - {self.quantity}x ({self.rental_start_date} to {self.return_date})"

    @property
    def is_overdue(self):
        """Check if the rental is overdue."""
        if self.is_returned:
            return False
        return timezone.now().date() > self.return_date

    @property
    def days_overdue(self):
        """Get number of days overdue."""
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.return_date).days

    def mark_returned(self):
        """Mark the rental as returned and restore stock."""
        if not self.is_returned:
            # Restore stock to product
            self.product.stock += self.quantity
            self.product.save(update_fields=['stock'])
            
            self.is_returned = True
            self.returned_at = timezone.now()
            self.save()


class ProductImage(models.Model):
    """Product images with ordering support."""
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-is_primary']
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):
        # If this is set as primary, remove primary from other images
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        # If this is the first image, make it primary
        if not self.pk and not ProductImage.objects.filter(product=self.product).exists():
            self.is_primary = True
        super().save(*args, **kwargs)


class SiteSettings(models.Model):
    """Singleton model for site-wide settings."""
    site_name = models.CharField(max_length=100, default='VerzendConnect')
    site_tagline = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    
    # Contact Information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Social Media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    
    # Business Settings
    currency = models.CharField(max_length=3, default='EUR')
    currency_symbol = models.CharField(max_length=5, default='€')
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Footer
    footer_text = models.TextField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class FAQ(models.Model):
    """Frequently Asked Questions."""
    question = models.CharField(max_length=500)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0, help_text="Order in which FAQ appears (lower numbers first)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'question']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class RentalTerms(models.Model):
    """Rental Terms and Conditions - Singleton model."""
    title = models.CharField(max_length=200, default='Rental Terms and Conditions')
    content = models.TextField(help_text="Full terms and conditions content. HTML is allowed.")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rental Terms and Conditions'
        verbose_name_plural = 'Rental Terms and Conditions'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_terms(cls):
        obj, created = cls.objects.get_or_create(pk=1, defaults={'title': 'Rental Terms and Conditions'})
        return obj

