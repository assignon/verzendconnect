from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from apps.orders.models import Order
from .models import Payment, Support
from .services import MollieService


class PaymentProcessView(View):
    """Initiate payment with Mollie."""
    
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        
        if order.payment_status == 'paid':
            return redirect('orders:success', order_number=order_number)
        
        # Create Mollie payment
        mollie_service = MollieService()
        
        try:
            payment = mollie_service.create_payment(
                order=order,
                method=order.payment_method,
                redirect_url=request.build_absolute_uri(f'/payments/return/{order_number}/'),
                webhook_url=request.build_absolute_uri('/payments/webhook/'),
            )
            
            # Check if checkout URL was created
            if not payment.mollie_checkout_url:
                raise ValueError("Mollie checkout URL is empty")
            
            # Redirect to Mollie checkout
            return redirect(payment.mollie_checkout_url)
            
        except Exception as e:
            import traceback
            print(f"Payment processing error: {str(e)}")
            print(traceback.format_exc())
            order.payment_status = 'failed'
            order.save()
            return redirect('orders:failed', order_number=order_number)


@method_decorator(csrf_exempt, name='dispatch')
class MollieWebhookView(View):
    """Handle Mollie payment webhooks."""
    
    def post(self, request):
        payment_id = request.POST.get('id')
        
        if not payment_id:
            return HttpResponse(status=400)
        
        try:
            payment = Payment.objects.get(mollie_payment_id=payment_id)
        except Payment.DoesNotExist:
            return HttpResponse(status=404)
        
        # Update payment status from Mollie
        mollie_service = MollieService()
        mollie_service.update_payment_status(payment)
        
        return HttpResponse(status=200)


@method_decorator(csrf_exempt, name='dispatch')
class MollieSupportWebhookView(View):
    """Handle Mollie payment webhooks for support/donations."""
    
    def post(self, request):
        payment_id = request.POST.get('id')
        
        if not payment_id:
            return HttpResponse(status=400)
        
        try:
            support = Support.objects.get(mollie_payment_id=payment_id)
        except Support.DoesNotExist:
            return HttpResponse(status=404)
        
        # Update support status from Mollie
        mollie_service = MollieService()
        mollie_service.update_support_status(support)
        
        return HttpResponse(status=200)


class PaymentReturnView(View):
    """Handle return from Mollie payment."""
    
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        
        # Check latest payment status
        payment = order.payments.order_by('-created_at').first()
        
        if payment:
            mollie_service = MollieService()
            mollie_service.update_payment_status(payment)
            
            if payment.status == 'paid':
                return redirect('orders:success', order_number=order_number)
        
        # If not paid, show order status page
        if order.payment_status == 'paid':
            return redirect('orders:success', order_number=order_number)
        else:
            return redirect('orders:failed', order_number=order_number)

