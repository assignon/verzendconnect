from django.urls import path
from django.http import JsonResponse
from . import views


def health_check(request):
    """Health check endpoint for Docker/load balancer."""
    return JsonResponse({'status': 'healthy'})


app_name = 'core'

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('', views.HomeView.as_view(), name='home'),
        path('about/', views.AboutView.as_view(), name='about'),
        path('faq/', views.FAQView.as_view(), name='faq'),
        path('rental-terms/', views.RentalTermsView.as_view(), name='rental_terms'),
        path('services/', views.ServicesView.as_view(), name='services'),
        path('support/', views.SupportView.as_view(), name='support'),
        path('support/return/<int:support_id>/', views.SupportReturnView.as_view(), name='support_return'),
        path('support/qr-code/', views.generate_qr_code, name='support_qr_code'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('event/<slug:slug>/', views.EventTypeDetailView.as_view(), name='event_type_detail'),
    path('search/', views.SearchView.as_view(), name='search'),
]

