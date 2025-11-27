from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Q
from .models import Product, Category, EventType


class HomeView(TemplateView):
    """Homepage with featured products, categories, and event types."""
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(
            is_active=True, 
            is_featured=True
        ).select_related('category').prefetch_related('images')[:8]
        context['featured_categories'] = Category.objects.filter(
            is_active=True, 
            is_featured=True
        )[:6]
        context['event_types'] = EventType.objects.filter(is_active=True)[:6]
        context['latest_products'] = Product.objects.filter(
            is_active=True
        ).select_related('category').prefetch_related('images')[:8]
        return context


class ProductListView(ListView):
    """List all products with filtering and search."""
    model = Product
    template_name = 'core/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
        
        # Category filter
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Event type filter
        event_slug = self.request.GET.get('event')
        if event_slug:
            queryset = queryset.filter(event_types__slug=event_slug)
        
        # Price filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Availability filter
        available_only = self.request.GET.get('available')
        if available_only:
            queryset = queryset.filter(is_available=True, stock__gt=0)
        
        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'name':
            queryset = queryset.order_by('name')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['event_types'] = EventType.objects.filter(is_active=True)
        context['current_category'] = self.request.GET.get('category')
        context['current_event'] = self.request.GET.get('event')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        return context


class ProductDetailView(DetailView):
    """Product detail page."""
    model = Product
    template_name = 'core/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'event_types')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Related products from same category
        context['related_products'] = Product.objects.filter(
            is_active=True,
            category=self.object.category
        ).exclude(id=self.object.id).prefetch_related('images')[:4]
        return context


class CategoryDetailView(DetailView):
    """Category page with products."""
    model = Category
    template_name = 'core/category_detail.html'
    context_object_name = 'category'

    def get_queryset(self):
        return Category.objects.filter(is_active=True).prefetch_related('event_types')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.filter(
            is_active=True,
            category=self.object
        ).select_related('category').prefetch_related('images')
        
        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        if sort == 'price_asc':
            products = products.order_by('price')
        elif sort == 'price_desc':
            products = products.order_by('-price')
        elif sort == 'name':
            products = products.order_by('name')
        else:
            products = products.order_by('-created_at')
        
        context['products'] = products
        context['subcategories'] = self.object.subcategories.filter(is_active=True)
        return context


class EventTypeDetailView(DetailView):
    """Event type page with products."""
    model = EventType
    template_name = 'core/event_type_detail.html'
    context_object_name = 'event_type'

    def get_queryset(self):
        return EventType.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(
            is_active=True,
            event_types=self.object
        ).select_related('category').prefetch_related('images')
        context['categories'] = Category.objects.filter(
            is_active=True,
            event_types=self.object
        )
        return context


class SearchView(ListView):
    """Search results page."""
    model = Product
    template_name = 'core/search.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            return Product.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(category__name__icontains=query),
                is_active=True
            ).select_related('category').prefetch_related('images')
        return Product.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

