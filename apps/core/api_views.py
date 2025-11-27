from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from .models import Product


class SearchAPIView(View):
    """API endpoint for live search."""
    
    def get(self, request):
        query = request.GET.get('q', '')
        results = []
        
        if query and len(query) >= 2:
            products = Product.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                is_active=True
            ).select_related('category').prefetch_related('images')[:10]
            
            for product in products:
                image = product.primary_image
                results.append({
                    'id': product.id,
                    'name': product.name,
                    'price': str(product.current_price),
                    'url': product.get_absolute_url(),
                    'image': image.image.url if image and image.image else '/static/images/placeholder.svg',
                    'category': product.category.name,
                })
        
        return JsonResponse({'results': results})


class ProductListAPIView(View):
    """API endpoint for products."""
    
    def get(self, request):
        products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')[:20]
        
        results = []
        for product in products:
            image = product.primary_image
            results.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': str(product.price),
                'sale_price': str(product.sale_price) if product.sale_price else None,
                'url': product.get_absolute_url(),
                'image': image.image.url if image and image.image else '/static/images/placeholder.svg',
                'category': product.category.name,
                'in_stock': product.in_stock,
            })
        
        return JsonResponse({'products': results})

