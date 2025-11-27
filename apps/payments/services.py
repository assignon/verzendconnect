from django.conf import settings
from django.utils import timezone
from mollie.api.client import Client
from .models import Payment


class MollieService:
    """Service class for Mollie payment integration."""
    
    def __init__(self):
        self.client = Client()
        self.client.set_api_key(settings.MOLLIE_API_KEY)
    
    def create_payment(self, order, method='ideal', redirect_url='', webhook_url=''):
        """Create a new Mollie payment."""
        
        # Map internal method names to Mollie method names
        method_mapping = {
            'ideal': 'ideal',
            'paypal': 'paypal',
            'creditcard': 'creditcard',
            'banktransfer': 'banktransfer',
        }
        
        mollie_method = method_mapping.get(method, 'ideal')
        
        # Create payment in Mollie
        mollie_payment = self.client.payments.create({
            'amount': {
                'currency': 'EUR',
                'value': f'{order.total:.2f}',
            },
            'description': f'Order #{order.order_number}',
            'redirectUrl': redirect_url,
            'webhookUrl': webhook_url,
            'method': mollie_method,
            'metadata': {
                'order_number': order.order_number,
                'order_id': order.id,
            },
        })
        
        # Store payment in database
        payment = Payment.objects.create(
            order=order,
            mollie_payment_id=mollie_payment['id'],
            mollie_checkout_url=mollie_payment['_links']['checkout']['href'] if mollie_payment.is_open() else '',
            method=method,
            status='open',
            amount=order.total,
            description=f'Order #{order.order_number}',
        )
        
        # Update order with payment ID
        order.payment_id = mollie_payment['id']
        order.save(update_fields=['payment_id'])
        
        return payment
    
    def update_payment_status(self, payment):
        """Update payment status from Mollie."""
        
        mollie_payment = self.client.payments.get(payment.mollie_payment_id)
        
        # Map Mollie status to our status
        status_mapping = {
            'open': 'open',
            'pending': 'pending',
            'authorized': 'authorized',
            'paid': 'paid',
            'failed': 'failed',
            'expired': 'expired',
            'canceled': 'canceled',
        }
        
        new_status = status_mapping.get(mollie_payment['status'], 'pending')
        payment.status = new_status
        
        if mollie_payment['method']:
            payment.method = mollie_payment['method']
        
        if new_status == 'paid':
            payment.paid_at = timezone.now()
            
            # Update order status
            order = payment.order
            order.payment_status = 'paid'
            order.status = 'paid'
            order.paid_at = timezone.now()
            order.save()
            
            # TODO: Send order confirmation email via Celery
            # TODO: Create admin notification
        
        elif new_status in ['failed', 'expired', 'canceled']:
            order = payment.order
            order.payment_status = 'failed'
            order.save()
        
        payment.save()
        return payment
    
    def refund_payment(self, payment, amount=None, reason=''):
        """Create a refund for a payment."""
        from .models import Refund
        
        if amount is None:
            amount = payment.amount
        
        mollie_refund = self.client.payment_refunds.with_parent_id(
            payment.mollie_payment_id
        ).create({
            'amount': {
                'currency': 'EUR',
                'value': f'{amount:.2f}',
            },
        })
        
        refund = Refund.objects.create(
            payment=payment,
            mollie_refund_id=mollie_refund['id'],
            amount=amount,
            reason=reason,
            status=mollie_refund['status'],
        )
        
        # Update order status if full refund
        if amount >= payment.amount:
            order = payment.order
            order.payment_status = 'refunded'
            order.status = 'refunded'
            order.save()
            
            payment.status = 'refunded'
            payment.save()
        
        return refund

