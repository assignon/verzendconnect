from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from apps.orders.models import Order
from apps.core.models import Product, Category
from apps.accounts.models import CustomUser


@method_decorator(staff_member_required, name='dispatch')
class DashboardView(TemplateView):
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
        
        # Recent Orders
        context['recent_orders'] = Order.objects.select_related('user').order_by('-created_at')[:10]
        
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


@method_decorator(staff_member_required, name='dispatch')
class ReportsView(TemplateView):
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
        
        # Average order value
        context['average_order_value'] = Order.objects.filter(
            payment_status='paid'
        ).aggregate(avg=Avg('total'))['avg'] or 0
        
        return context

