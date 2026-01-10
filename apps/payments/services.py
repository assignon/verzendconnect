from django.conf import settings
from django.utils import timezone
from mollie.api.client import Client
from .models import Payment, Support


class MollieService:
    """Service class for Mollie payment integration."""
    
    def __init__(self):
        self.client = Client()
        self.client.set_api_key(settings.MOLLIE_API_KEY)
    
    def get_available_payment_methods(self, amount=None, currency='EUR'):
        """Get list of available payment methods from Mollie."""
        try:
            # Check if API key is set
            if not settings.MOLLIE_API_KEY:
                raise ValueError("MOLLIE_API_KEY is not set in settings")
            
            # Fetch methods from Mollie (with amount/currency to get only applicable methods)
            # The methods.list() can take amount and currency as parameters
            if amount:
                methods = self.client.methods.list(
                    amount={'currency': currency, 'value': f'{amount:.2f}'}
                )
            else:
                methods = self.client.methods.list()
            available_methods = []
            
            # Payment method display info
            method_info = {
                'ideal': {
                    'name': 'iDEAL',
                    'description': 'Pay directly from your Dutch bank account',
                    'icon': 'https://www.mollie.com/external/icons/payment-methods/ideal.svg',
                },
                'paypal': {
                    'name': 'PayPal',
                    'description': 'Pay with your PayPal account',
                    'icon': 'https://www.mollie.com/external/icons/payment-methods/paypal.svg',
                },
                'creditcard': {
                    'name': 'Credit Card',
                    'description': 'Visa, Mastercard, American Express',
                    'icon': 'https://www.mollie.com/external/icons/payment-methods/visa.svg',
                    'icons': [
                        'https://www.mollie.com/external/icons/payment-methods/visa.svg',
                        'https://www.mollie.com/external/icons/payment-methods/mastercard.svg',
                    ],
                },
                'banktransfer': {
                    'name': 'Bank Transfer',
                    'description': 'Pay via manual bank transfer',
                    'icon': 'https://www.mollie.com/external/icons/payment-methods/banktransfer.svg',
                },
            }
            
            # Process methods from Mollie
            # Mollie returns a list-like object, iterate through it
            for method in methods:
                # Handle both dict and object access
                method_id = method['id'] if isinstance(method, dict) else getattr(method, 'id', None)
                
                if method_id and method_id in method_info:
                    info = method_info[method_id].copy()
                    info['id'] = method_id
                    available_methods.append(info)
            
            # If no methods found, return default
            if not available_methods:
                return [
                    {
                        'id': 'ideal',
                        'name': 'iDEAL',
                        'description': 'Pay directly from your Dutch bank account',
                        'icon': 'https://www.mollie.com/external/icons/payment-methods/ideal.svg',
                    }
                ]
            
            return available_methods
            
        except Exception as e:
            import traceback
            print(f"Error fetching available payment methods from Mollie: {e}")
            print(traceback.format_exc())
            # Return default methods if API call fails
            return [
                {
                    'id': 'ideal',
                    'name': 'iDEAL',
                    'description': 'Pay directly from your Dutch bank account',
                    'icon': 'https://www.mollie.com/external/icons/payment-methods/ideal.svg',
                }
            ]
    
    def create_payment(self, order, method='ideal', redirect_url='', webhook_url=''):
        """Create a new Mollie payment."""
        
        # Check if API key is set
        if not settings.MOLLIE_API_KEY:
            raise ValueError("MOLLIE_API_KEY is not set in settings")
        
        # Map internal method names to Mollie method names
        method_mapping = {
            'ideal': 'ideal',
            'paypal': 'paypal',
            'creditcard': 'creditcard',
            'banktransfer': 'banktransfer',
        }
        
        mollie_method = method_mapping.get(method, 'ideal')
        
        # Build payment data
        payment_data = {
            'amount': {
                'currency': 'EUR',
                'value': f'{order.total:.2f}',
            },
            'description': f'Order #{order.order_number}',
            'redirectUrl': redirect_url,
            'method': mollie_method,
            'metadata': {
                'order_number': order.order_number,
                'order_id': order.id,
            },
        }
        
        # Only add webhook URL if it's a public URL (not localhost)
        # Mollie requires webhooks to be publicly accessible
        if webhook_url and 'localhost' not in webhook_url and '127.0.0.1' not in webhook_url:
            payment_data['webhookUrl'] = webhook_url
        
        # Create payment in Mollie
        mollie_payment = self.client.payments.create(payment_data)
        
        # Extract payment ID and checkout URL from Mollie response
        # Mollie Python client returns a Payment object with dict-like access
        payment_id = str(mollie_payment['id'])
        
        # Get checkout URL from _links
        links = mollie_payment['_links']
        checkout_url = links['checkout']['href'] if 'checkout' in links else ''
        
        if not checkout_url:
            # Fallback: construct URL from payment ID
            checkout_url = f"https://www.mollie.com/checkout/select-method/{payment_id}"
        
        # Store payment in database
        payment = Payment.objects.create(
            order=order,
            mollie_payment_id=payment_id,
            mollie_checkout_url=checkout_url,
            method=method,
            status='open',
            amount=order.total,
            description=f'Order #{order.order_number}',
        )
        
        # Update order with payment ID
        order.payment_id = payment_id
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
            
            # Send order confirmation email to customer
            from apps.notifications.tasks import send_order_confirmation_email, send_payment_confirmation_email
            try:
                send_order_confirmation_email(order.id)
                send_payment_confirmation_email(order.id)
            except Exception as e:
                print(f"Failed to send confirmation emails: {e}")
        
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
    
    def create_support_payment(self, support, method='ideal', redirect_url='', webhook_url=''):
        """Create a new Mollie payment for support/donation."""
        
        # Check if API key is set
        if not settings.MOLLIE_API_KEY:
            raise ValueError("MOLLIE_API_KEY is not set in settings")
        
        # Map internal method names to Mollie method names
        method_mapping = {
            'ideal': 'ideal',
            'paypal': 'paypal',
            'creditcard': 'creditcard',
            'banktransfer': 'banktransfer',
        }
        
        mollie_method = method_mapping.get(method, 'ideal')
        
        # Build payment data
        payment_data = {
            'amount': {
                'currency': support.currency,
                'value': f'{support.amount:.2f}',
            },
            'description': f'Support Verzend Connect - €{support.amount:.2f}',
            'redirectUrl': redirect_url,
            'method': mollie_method,
            'metadata': {
                'support_id': support.id,
                'type': 'support',
            },
        }
        
        # Only add webhook URL if it's a public URL (not localhost)
        if webhook_url and 'localhost' not in webhook_url and '127.0.0.1' not in webhook_url:
            payment_data['webhookUrl'] = webhook_url
        
        # Create payment in Mollie
        mollie_payment = self.client.payments.create(payment_data)
        
        # Extract payment ID and checkout URL from Mollie response
        payment_id = str(mollie_payment['id'])
        
        # Get checkout URL from _links
        links = mollie_payment['_links']
        checkout_url = links['checkout']['href'] if 'checkout' in links else ''
        
        if not checkout_url:
            # Fallback: construct URL from payment ID
            checkout_url = f"https://www.mollie.com/checkout/select-method/{payment_id}"
        
        # Update support record with payment info
        support.mollie_payment_id = payment_id
        support.mollie_checkout_url = checkout_url
        support.status = 'open'
        support.save()
        
        return support
    
    def update_support_status(self, support):
        """Update support payment status from Mollie."""
        
        if not support.mollie_payment_id:
            return support
        
        mollie_payment = self.client.payments.get(support.mollie_payment_id)
        
        # Map Mollie status to our status
        status_mapping = {
            'open': 'open',
            'pending': 'pending',
            'paid': 'paid',
            'failed': 'failed',
            'expired': 'expired',
            'canceled': 'canceled',
        }
        
        new_status = status_mapping.get(mollie_payment['status'], 'pending')
        support.status = new_status
        
        if new_status == 'paid':
            support.paid_at = timezone.now()
        
        support.save()
        return support

