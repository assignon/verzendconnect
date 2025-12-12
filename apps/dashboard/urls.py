from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='index'),
    path('reports/', views.ReportsView.as_view(), name='reports'),

    # Product Management
    path('products/', views.ProductListView.as_view(), name='products'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/add/', views.ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Category Management
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Event Types Management
    path('event-types/', views.EventTypeListView.as_view(), name='event_types'),
    path('event-types/<int:pk>/', views.EventTypeDetailView.as_view(), name='event_type_detail'),
    path('event-types/add/', views.EventTypeCreateView.as_view(), name='event_type_add'),
    path('event-types/<int:pk>/edit/', views.EventTypeUpdateView.as_view(), name='event_type_edit'),
    path('event-types/<int:pk>/delete/', views.EventTypeDeleteView.as_view(), name='event_type_delete'),

    # Order Management
    path('orders/', views.OrderListView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]

