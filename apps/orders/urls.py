from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart
    path('', views.CartView.as_view(), name='cart'),
    path('add/', views.CartAddView.as_view(), name='cart_add'),
    path('update/', views.CartUpdateView.as_view(), name='cart_update'),
    path('remove/', views.CartRemoveView.as_view(), name='cart_remove'),
    path('clear/', views.CartClearView.as_view(), name='cart_clear'),
    
    # Checkout
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('checkout/info/', views.CheckoutInfoView.as_view(), name='checkout_info'),
    path('checkout/shipping/', views.CheckoutShippingView.as_view(), name='checkout_shipping'),
    path('checkout/payment/', views.CheckoutPaymentView.as_view(), name='checkout_payment'),
    path('checkout/confirm/', views.CheckoutConfirmView.as_view(), name='checkout_confirm'),
    
    # Order confirmation
    path('order/<str:order_number>/success/', views.OrderSuccessView.as_view(), name='success'),
    path('order/<str:order_number>/failed/', views.OrderFailedView.as_view(), name='failed'),
]

