from django.urls import path
from . import api_views

urlpatterns = [
    path('search/', api_views.SearchAPIView.as_view(), name='api_search'),
    path('products/', api_views.ProductListAPIView.as_view(), name='api_products'),
]

