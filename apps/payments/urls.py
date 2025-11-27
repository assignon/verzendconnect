from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('process/<str:order_number>/', views.PaymentProcessView.as_view(), name='process'),
    path('webhook/', views.MollieWebhookView.as_view(), name='webhook'),
    path('return/<str:order_number>/', views.PaymentReturnView.as_view(), name='return'),
]

