from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from apps.orders.models import Order
from apps.core.models import Product, Category, ProductImage, EventType, RentalRecord, FAQ, RentalTerms, Services, SiteSettings
from apps.accounts.models import CustomUser
from .forms import CompanyInfoForm


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only superusers can access the view."""
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Superuser privileges required.')
        return redirect('core:home')


class DashboardView(SuperuserRequiredMixin, TemplateView):
    """Admin dashboard with analytics overview."""
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Date ranges
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)
        this_month_start = today.replace(day=1)
        
        # Order Statistics
        context['total_orders'] = Order.objects.count()
        context['orders_today'] = Order.objects.filter(created_at__date=today).count()
        context['orders_this_week'] = Order.objects.filter(created_at__date__gte=last_7_days).count()
        context['orders_this_month'] = Order.objects.filter(created_at__date__gte=this_month_start).count()
        
        # Revenue Statistics
        context['total_revenue'] = Order.objects.filter(
            payment_status='paid'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        context['revenue_today'] = Order.objects.filter(
            payment_status='paid',
            created_at__date=today
        ).aggregate(total=Sum('total'))['total'] or 0
        
        context['revenue_this_week'] = Order.objects.filter(
            payment_status='paid',
            created_at__date__gte=last_7_days
        ).aggregate(total=Sum('total'))['total'] or 0
        
        context['revenue_this_month'] = Order.objects.filter(
            payment_status='paid',
            created_at__date__gte=this_month_start
        ).aggregate(total=Sum('total'))['total'] or 0
        
        # Customer Statistics
        context['total_customers'] = CustomUser.objects.filter(is_staff=False).count()
        context['new_customers_this_month'] = CustomUser.objects.filter(
            is_staff=False,
            date_joined__date__gte=this_month_start
        ).count()
        
        # Product Statistics
        context['total_products'] = Product.objects.filter(is_active=True).count()
        context['low_stock_products'] = Product.objects.filter(
            is_active=True,
            stock__lte=5,
            stock__gt=0
        ).count()
        context['out_of_stock_products'] = Product.objects.filter(
            is_active=True,
            stock=0
        ).count()
        
        # Recent Orders (limit to 5)
        context['recent_orders'] = Order.objects.select_related('user').order_by('-created_at')[:5]
        
        # Order Status Distribution
        context['pending_orders'] = Order.objects.filter(status='pending').count()
        context['processing_orders'] = Order.objects.filter(status__in=['paid', 'confirmed', 'preparing']).count()
        context['completed_orders'] = Order.objects.filter(status__in=['delivered', 'completed']).count()
        
        # Sales by Day (last 7 days)
        sales_by_day = Order.objects.filter(
            payment_status='paid',
            created_at__date__gte=last_7_days
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('date')
        
        context['sales_chart_labels'] = [s['date'].strftime('%b %d') for s in sales_by_day]
        context['sales_chart_data'] = [float(s['total']) for s in sales_by_day]
        
        # Top Products
        context['top_products'] = Product.objects.filter(
            is_active=True
        ).annotate(
            order_count=Count('orderitem')
        ).order_by('-order_count')[:5]
        
        # Top Categories
        context['top_categories'] = Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products')
        ).order_by('-product_count')[:5]
        
        return context


class ReportsView(SuperuserRequiredMixin, TemplateView):
    """Detailed reports view."""
    template_name = 'dashboard/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Monthly sales for the past 12 months
        twelve_months_ago = timezone.now() - timedelta(days=365)
        monthly_sales = Order.objects.filter(
            payment_status='paid',
            created_at__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('month')
        
        context['monthly_chart_labels'] = [s['month'].strftime('%b %Y') for s in monthly_sales]
        context['monthly_chart_data'] = [float(s['total']) for s in monthly_sales]
        context['monthly_order_counts'] = [s['count'] for s in monthly_sales]
        
        # Prepare monthly data for table with average order value
        context['monthly_data'] = [
            (
                s['month'].strftime('%b %Y'),
                float(s['total']),
                s['count'],
                float(s['total']) / s['count'] if s['count'] > 0 else 0.0
            )
            for s in monthly_sales
        ]
        
        # Calculate totals for 12-month period
        context['twelve_month_revenue'] = sum(float(s['total']) for s in monthly_sales)
        context['twelve_month_orders'] = sum(s['count'] for s in monthly_sales)
        
        # Average order value
        context['average_order_value'] = Order.objects.filter(
            payment_status='paid'
        ).aggregate(avg=Avg('total'))['avg'] or 0

        return context


# Product Management Views
class ProductListView(SuperuserRequiredMixin, ListView):
    """List all products for admin management."""
    model = Product
    template_name = 'dashboard/products/list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = Product.objects.select_related('category').prefetch_related('images')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__name__icontains=search)
            )
        return queryset.order_by('-created_at')


class ProductCreateView(SuperuserRequiredMixin, CreateView):
    """Create new product."""
    model = Product
    template_name = 'dashboard/products/form.html'
    fields = ['name', 'category', 'event_types', 'price', 'sale_price', 'stock',
              'short_description', 'description', 'is_available', 'is_active', 'is_featured',
              'rental_start_date', 'rental_end_date']
    success_url = reverse_lazy('dashboard:products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Product'
        context['categories'] = Category.objects.filter(is_active=True)
        context['event_types'] = EventType.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        product = form.save()
        # Handle primary image upload
        primary_image_file = self.request.FILES.get('primary_image')
        if primary_image_file:
            from apps.core.models import ProductImage
            ProductImage.objects.create(
                product=product,
                image=primary_image_file,
                alt_text=product.name,
                is_primary=True
            )
        messages.success(self.request, f'Product "{product.name}" created successfully.')
        return super().form_valid(form)


class ProductUpdateView(SuperuserRequiredMixin, UpdateView):
    """Update existing product."""
    model = Product
    template_name = 'dashboard/products/form.html'
    fields = ['name', 'category', 'event_types', 'price', 'sale_price', 'stock',
              'short_description', 'description', 'is_available', 'is_active', 'is_featured',
              'rental_start_date', 'rental_end_date']
    success_url = reverse_lazy('dashboard:products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Product'
        context['categories'] = Category.objects.filter(is_active=True)
        context['event_types'] = EventType.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        product = form.save()
        # Handle primary image upload
        primary_image_file = self.request.FILES.get('primary_image')
        if primary_image_file:
            from apps.core.models import ProductImage
            # Remove existing primary images
            ProductImage.objects.filter(product=product, is_primary=True).update(is_primary=False)
            # Create or update primary image
            ProductImage.objects.update_or_create(
                product=product,
                is_primary=True,
                defaults={
                    'image': primary_image_file,
                    'alt_text': product.name,
                }
            )
        messages.success(self.request, f'Product "{product.name}" updated successfully.')
        return super().form_valid(form)


class ProductDetailView(SuperuserRequiredMixin, DetailView):
    """View product details for admin."""
    model = Product
    template_name = 'dashboard/products/detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_images'] = self.object.images.all()
        if self.object.sale_price:
            context['savings'] = self.object.price - self.object.sale_price
            context['discount_percentage'] = round((context['savings'] / self.object.price) * 100)
        return context


class ProductDeleteView(SuperuserRequiredMixin, DeleteView):
    """Delete product."""
    model = Product
    template_name = 'dashboard/products/delete.html'
    success_url = reverse_lazy('dashboard:products')

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        messages.success(request, f'Product "{product.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Category Management Views
class CategoryListView(SuperuserRequiredMixin, ListView):
    """List all categories for admin management."""
    model = Category
    template_name = 'dashboard/categories/list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        queryset = Category.objects.prefetch_related('products')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset.order_by('-created_at')


class CategoryCreateView(SuperuserRequiredMixin, CreateView):
    """Create new category."""
    model = Category
    template_name = 'dashboard/categories/form.html'
    fields = ['name', 'description', 'image', 'parent', 'event_types', 'is_active', 'is_featured', 'order']
    success_url = reverse_lazy('dashboard:categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Category'
        context['parent_categories'] = Category.objects.filter(parent__isnull=True, is_active=True)
        context['event_types'] = EventType.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class CategoryUpdateView(SuperuserRequiredMixin, UpdateView):
    """Update existing category."""
    model = Category
    template_name = 'dashboard/categories/form.html'
    fields = ['name', 'description', 'image', 'parent', 'event_types', 'is_active', 'is_featured', 'order']
    success_url = reverse_lazy('dashboard:categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Category'
        context['parent_categories'] = Category.objects.filter(
            parent__isnull=True,
            is_active=True
        ).exclude(pk=self.object.pk)
        context['event_types'] = EventType.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class CategoryDetailView(SuperuserRequiredMixin, DetailView):
    """View category details for admin."""
    model = Category
    template_name = 'dashboard/categories/detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subcategories'] = self.object.subcategories.filter(is_active=True)
        context['products'] = self.object.products.filter(is_active=True)
        return context


class CategoryDeleteView(SuperuserRequiredMixin, DeleteView):
    """Delete category."""
    model = Category
    template_name = 'dashboard/categories/delete.html'
    success_url = reverse_lazy('dashboard:categories')

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        messages.success(request, f'Category "{category.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Event Types Management Views
class EventTypeListView(SuperuserRequiredMixin, ListView):
    """List all event types for admin management."""
    model = EventType
    template_name = 'dashboard/event_types/list.html'
    context_object_name = 'event_types'
    paginate_by = 20

    def get_queryset(self):
        queryset = EventType.objects.prefetch_related('products')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset.order_by('-created_at')


class EventTypeCreateView(SuperuserRequiredMixin, CreateView):
    """Create new event type."""
    model = EventType
    template_name = 'dashboard/event_types/form.html'
    fields = ['name', 'description', 'icon', 'image', 'is_active']
    success_url = reverse_lazy('dashboard:event_types')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Event Type'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Event type "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class EventTypeUpdateView(SuperuserRequiredMixin, UpdateView):
    """Update existing event type."""
    model = EventType
    template_name = 'dashboard/event_types/form.html'
    fields = ['name', 'description', 'icon', 'image', 'is_active']
    success_url = reverse_lazy('dashboard:event_types')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Event Type'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Event type "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class EventTypeDetailView(SuperuserRequiredMixin, DetailView):
    """View event type details for admin."""
    model = EventType
    template_name = 'dashboard/event_types/detail.html'
    context_object_name = 'event_type'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = self.object.categories.filter(is_active=True)
        context['products'] = self.object.products.filter(is_active=True)
        return context


class EventTypeDeleteView(SuperuserRequiredMixin, DeleteView):
    """Delete event type."""
    model = EventType
    template_name = 'dashboard/event_types/delete.html'
    success_url = reverse_lazy('dashboard:event_types')

    def delete(self, request, *args, **kwargs):
        event_type = self.get_object()
        messages.success(request, f'Event type "{event_type.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Order Management Views
class OrderListView(SuperuserRequiredMixin, ListView):
    """List all orders for admin management."""
    model = Order
    template_name = 'dashboard/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = Order.objects.select_related('user').prefetch_related('items__product')
        status = self.request.GET.get('status')
        payment_status = self.request.GET.get('payment_status')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(email__icontains=search) |
                Q(shipping_first_name__icontains=search) |
                Q(shipping_last_name__icontains=search)
            )

        return queryset.order_by('-created_at')


class OrderDetailView(SuperuserRequiredMixin, DetailView):
    """View order details for admin with status update capability."""
    model = Order
    template_name = 'dashboard/orders/detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_items'] = self.object.items.select_related('product').all()
        # Get status choices from the model
        status_field = Order._meta.get_field('status')
        context['status_choices'] = status_field.choices
        return context

    def post(self, request, *args, **kwargs):
        """Handle status update."""
        self.object = self.get_object()
        new_status = request.POST.get('status')
        
        # Get valid status choices
        status_field = Order._meta.get_field('status')
        valid_statuses = [choice[0] for choice in status_field.choices]
        
        if new_status and new_status in valid_statuses:
            old_status = self.object.status
            old_status_display = self.object.get_status_display()
            self.object.status = new_status
            self.object.save(update_fields=['status'])
            new_status_display = self.object.get_status_display()
            messages.success(request, f'Order status updated from {old_status_display} to {new_status_display}.')
            
            # Send status update notification email to customer if status actually changed
            if old_status != new_status:
                from apps.notifications.tasks import send_order_status_update_email
                try:
                    send_order_status_update_email(self.object.id)
                except Exception as e:
                    print(f"Failed to send status update email: {e}")
        else:
            messages.error(request, 'Invalid status selected.')
        
        return redirect('dashboard:order_detail', pk=self.object.pk)


# Stock Management Views
class StockManagementView(SuperuserRequiredMixin, ListView):
    """View all rental records for stock management."""
    model = RentalRecord
    template_name = 'dashboard/stock/list.html'
    context_object_name = 'rentals'
    paginate_by = 20

    def get_queryset(self):
        queryset = RentalRecord.objects.select_related('product', 'customer', 'order_item__order')
        
        # Filter options
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        product_id = self.request.GET.get('product')
        
        if status == 'active':
            queryset = queryset.filter(is_returned=False)
        elif status == 'returned':
            queryset = queryset.filter(is_returned=True)
        elif status == 'overdue':
            today = timezone.now().date()
            queryset = queryset.filter(is_returned=False, return_date__lt=today)
        
        if search:
            queryset = queryset.filter(
                Q(product__name__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(customer_email__icontains=search)
            )
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset.order_by('-rental_start_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Stats
        context['total_rentals'] = RentalRecord.objects.count()
        context['active_rentals'] = RentalRecord.objects.filter(is_returned=False).count()
        context['overdue_rentals'] = RentalRecord.objects.filter(
            is_returned=False, 
            return_date__lt=today
        ).count()
        context['returned_rentals'] = RentalRecord.objects.filter(is_returned=True).count()
        
        # Products for filter dropdown
        context['products'] = Product.objects.filter(is_active=True).order_by('name')
        
        return context


class RentalDetailView(SuperuserRequiredMixin, DetailView):
    """View rental record details."""
    model = RentalRecord
    template_name = 'dashboard/stock/detail.html'
    context_object_name = 'rental'


class RentalMarkReturnedView(SuperuserRequiredMixin, View):
    """Mark a rental as returned."""
    
    def post(self, request, pk):
        rental = get_object_or_404(RentalRecord, pk=pk)
        
        if rental.is_returned:
            messages.warning(request, 'This rental is already marked as returned.')
        else:
            rental.mark_returned()
            messages.success(request, f'Rental for {rental.product.name} marked as returned. Stock restored.')
        
        # Check if it's an AJAX request
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True})
        
        return redirect('dashboard:stock_management')


class ProductStockDetailView(SuperuserRequiredMixin, DetailView):
    """View stock details for a specific product."""
    model = Product
    template_name = 'dashboard/stock/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        today = timezone.now().date()
        
        # All rentals for this product
        context['all_rentals'] = product.rental_records.select_related(
            'customer', 'order_item__order'
        ).order_by('-rental_start_date')
        
        # Active rentals
        context['active_rentals'] = product.rental_records.filter(
            is_returned=False
        ).order_by('return_date')
        
        # Overdue rentals
        context['overdue_rentals'] = product.rental_records.filter(
            is_returned=False,
            return_date__lt=today
        )
        
        # Calculate current available stock
        context['available_stock'] = product.get_available_stock(today, today + timedelta(days=1))
        
        # Stock currently rented out
        rented_out = product.rental_records.filter(is_returned=False).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        context['rented_out'] = rented_out
        
        return context


# Overall Management Views (FAQ & Rental Terms)
class OverallManagementView(SuperuserRequiredMixin, TemplateView):
    """Overall management page with tabs for FAQ and Rental Terms."""
    template_name = 'dashboard/overall/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faqs'] = FAQ.objects.all().order_by('order', 'question')
        context['rental_terms'] = RentalTerms.get_terms()
        context['services'] = Services.get_services()
        context['active_tab'] = self.request.GET.get('tab', 'faq')
        return context


class FAQCreateView(SuperuserRequiredMixin, CreateView):
    """Create new FAQ."""
    model = FAQ
    template_name = 'dashboard/overall/faq_form.html'
    fields = ['question', 'answer', 'order', 'is_active']
    success_url = reverse_lazy('dashboard:overall')

    def get_success_url(self):
        return reverse_lazy('dashboard:overall') + '?tab=faq'


class FAQUpdateView(SuperuserRequiredMixin, UpdateView):
    """Update FAQ."""
    model = FAQ
    template_name = 'dashboard/overall/faq_form.html'
    fields = ['question', 'answer', 'order', 'is_active']
    success_url = reverse_lazy('dashboard:overall')

    def get_success_url(self):
        return reverse_lazy('dashboard:overall') + '?tab=faq'


class FAQDeleteView(SuperuserRequiredMixin, DeleteView):
    """Delete FAQ."""
    model = FAQ
    template_name = 'dashboard/overall/faq_delete.html'
    success_url = reverse_lazy('dashboard:overall')

    def get_success_url(self):
        return reverse_lazy('dashboard:overall') + '?tab=faq'

    def delete(self, request, *args, **kwargs):
        faq = self.get_object()
        messages.success(request, f'FAQ "{faq.question}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


class RentalTermsUpdateView(SuperuserRequiredMixin, UpdateView):
    """Update Rental Terms and Conditions."""
    model = RentalTerms
    template_name = 'dashboard/overall/rental_terms_form.html'
    fields = ['title', 'content', 'is_active']
    success_url = reverse_lazy('dashboard:overall')

    def get_object(self, queryset=None):
        return RentalTerms.get_terms()

    def get_success_url(self):
        return reverse_lazy('dashboard:overall') + '?tab=terms'

    def form_valid(self, form):
        messages.success(self.request, 'Rental Terms and Conditions updated successfully.')
        return super().form_valid(form)


class ServicesUpdateView(SuperuserRequiredMixin, UpdateView):
    """Update Services information."""
    model = Services
    template_name = 'dashboard/overall/services_form.html'
    fields = ['title', 'content', 'is_active']
    success_url = reverse_lazy('dashboard:overall')

    def get_object(self, queryset=None):
        return Services.get_services()

    def get_success_url(self):
        return reverse_lazy('dashboard:overall') + '?tab=services'

    def form_valid(self, form):
        messages.success(self.request, 'Services updated successfully.')
        return super().form_valid(form)


class CompanyInfoUpdateView(SuperuserRequiredMixin, UpdateView):
    """Update company contact information."""
    model = SiteSettings
    form_class = CompanyInfoForm
    template_name = 'dashboard/company_info.html'
    success_url = reverse_lazy('dashboard:company_info')

    def get_object(self, queryset=None):
        """Get or create the SiteSettings instance (singleton)."""
        obj, created = SiteSettings.objects.get_or_create(pk=1)
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Company information updated successfully.')
        return super().form_valid(form)

