"""
Core views for VerzendConnect.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.utils import translation
from .models import Product, Category, EventType, SiteSettings, FAQ, RentalTerms, Services


def robots_txt(request):
    """Generate robots.txt file."""
    site_url = getattr(settings, 'SITE_URL', 'https://verzendconnect.nl')
    sitemap_url = f"{site_url}/sitemap.xml"
    
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /accounts/
Disallow: /cart/checkout/
Disallow: /api/
Disallow: /i18n/

Sitemap: {sitemap_url}
"""
    return HttpResponse(content, content_type='text/plain')


@require_POST
def set_language_custom(request):
    """
    Custom language switching view that properly handles redirects
    with prefix_default_language=False.
    """
    language = request.POST.get('language')
    next_url = request.POST.get('next', '/')
    
    if language and language in dict(settings.LANGUAGES):
        # Set language in session (using the session key directly)
        request.session['django_language'] = language
        
        # Handle URL translation based on prefix_default_language setting
        # Since prefix_default_language=False, default language (Dutch/nl) has no prefix
        default_lang = settings.LANGUAGE_CODE
        
        # Parse the next_url to extract path and query string
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(next_url)
        path = parsed.path
        query_params = parse_qs(parsed.query)
        
        # Remove any existing language prefix from path
        for lang_code, _ in settings.LANGUAGES:
            if path.startswith(f'/{lang_code}/'):
                path = path[len(f'/{lang_code}/'):]
                if not path.startswith('/'):
                    path = '/' + path
                break
            elif path == f'/{lang_code}':
                path = '/'
                break
        
        # Add language prefix only if it's not the default language
        if language != default_lang:
            if not path.startswith('/'):
                path = '/' + path
            path = f'/{language}{path}'
        
        # Reconstruct URL with query parameters
        query_string = urlencode(query_params, doseq=True) if query_params else ''
        new_url = urlunparse((
            parsed.scheme or '',
            parsed.netloc or '',
            path,
            parsed.params,
            query_string,
            parsed.fragment
        ))
        
        # Remove leading // if present
        if new_url.startswith('//'):
            new_url = new_url[1:]
        
        # Activate the language for the response
        translation.activate(language)
        
        return HttpResponseRedirect(new_url)
    
    # Fallback
    return redirect('core:home')


class HomeView(TemplateView):
    """Homepage view."""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_types'] = EventType.objects.filter(is_active=True)[:6]
        context['featured_categories'] = Category.objects.filter(
            is_active=True, 
            parent__isnull=True
        ).prefetch_related('products')[:6]
        context['featured_products'] = Product.objects.filter(
            is_active=True, 
            is_featured=True
        ).select_related('category')[:8]
        context['latest_products'] = Product.objects.filter(
            is_active=True
        ).select_related('category').order_by('-created_at')[:8]
        return context


class ProductListView(ListView):
    """Product listing page with filters."""
    model = Product
    template_name = 'core/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')
        
        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # Category filter
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Event type filter
        event_slug = self.request.GET.get('event')
        if event_slug:
            queryset = queryset.filter(event_types__slug=event_slug)
        
        # Sorting
        sort = self.request.GET.get('sort', '')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort == '-created_at':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True, parent__isnull=True)
        context['event_types'] = EventType.objects.filter(is_active=True)
        return context


class ProductDetailView(DetailView):
    """Product detail page."""
    model = Product
    template_name = 'core/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        # Breadcrumb items for structured data
        site_url = getattr(settings, 'SITE_URL', 'https://verzendconnect.nl')
        context['breadcrumb_items'] = [
            {'name': 'Home', 'url': site_url},
            {'name': product.category.name, 'url': f"{site_url}{product.category.get_absolute_url()}"},
            {'name': product.name, 'url': f"{site_url}{product.get_absolute_url()}"},
        ]
        return context


class CategoryDetailView(DetailView):
    """Category detail page."""
    model = Category
    template_name = 'core/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        context['products'] = Product.objects.filter(
            category=category,
            is_active=True
        ).select_related('category')
        context['subcategories'] = category.subcategories.filter(is_active=True)
        return context


class EventTypeDetailView(DetailView):
    """Event type detail page."""
    model = EventType
    template_name = 'core/event_type_detail.html'
    context_object_name = 'event_type'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return EventType.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_type = self.object
        context['products'] = Product.objects.filter(
            event_types=event_type,
            is_active=True
        ).select_related('category')
        return context


class SearchView(ListView):
    """Search results page."""
    model = Product
    template_name = 'core/search.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if not query:
            return Product.objects.none()
        
        return Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).filter(is_active=True).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class AboutView(TemplateView):
    """About us page."""
    template_name = 'core/about.html'


class FAQView(TemplateView):
    """FAQ page."""
    template_name = 'core/faq.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faqs = FAQ.objects.filter(is_active=True).order_by('order', 'id')
        context['faqs'] = faqs
        
        # FAQPage structured data
        site_url = getattr(settings, 'SITE_URL', 'https://verzendconnect.nl')
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        
        for faq in faqs:
            faq_schema["mainEntity"].append({
                "@type": "Question",
                "name": faq.question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq.answer
                }
            })
        
        context['faq_schema'] = faq_schema
        return context


class RentalTermsView(TemplateView):
    """Rental terms and conditions page."""
    template_name = 'core/rental_terms.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rental_terms'] = RentalTerms.objects.filter(is_active=True).first()
        return context


class ServicesView(TemplateView):
    """Services page."""
    template_name = 'core/services.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = Services.get_services()
        return context
