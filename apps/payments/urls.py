from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('process/<str:order_number>/', views.PaymentProcessView.as_view(), name='process'),
    path('webhook/', views.MollieWebhookView.as_view(), name='webhook'),
    path('webhook-support/', views.MollieSupportWebhookView.as_view(), name='webhook_support'),
    path('return/<str:order_number>/', views.PaymentReturnView.as_view(), name='return'),
]

