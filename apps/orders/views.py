import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.core.models import Product
from .models import Cart, CartItem, Order, OrderItem
from .forms import CheckoutForm, ShippingForm


class CartMixin:
    """Mixin to get or create cart."""
    
    def get_cart(self, request):
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart


class CartView(CartMixin, View):
    """Display cart contents."""
    template_name = 'orders/cart.html'

    def get(self, request):
        cart = self.get_cart(request)
        return render(request, self.template_name, {'cart': cart})


class CartAddView(CartMixin, View):
    """Add item to cart (AJAX)."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
        except (json.JSONDecodeError, ValueError):
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)

        if not product.in_stock:
            return JsonResponse({'success': False, 'error': 'Product out of stock'}, status=400)

        cart = self.get_cart(request)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        # Check if AJAX request
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True,
                'cart_count': cart.items_count,
                'cart_total': float(cart.total),
                'message': f'{product.name} added to cart'
            })
        
        messages.success(request, f'{product.name} added to cart!')
        return redirect('orders:cart')


class CartUpdateView(CartMixin, View):
    """Update cart item quantity (AJAX)."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
        except (json.JSONDecodeError, ValueError):
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))

        cart = self.get_cart(request)
        
        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not in cart'}, status=404)

        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True,
                'cart_count': cart.items_count,
                'cart_total': float(cart.total),
                'item_total': float(cart_item.total) if quantity > 0 else 0
            })
        
        return redirect('orders:cart')


class CartRemoveView(CartMixin, View):
    """Remove item from cart (AJAX)."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
        except (json.JSONDecodeError, ValueError):
            product_id = request.POST.get('product_id')

        cart = self.get_cart(request)
        
        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
        except CartItem.DoesNotExist:
            pass

        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True,
                'cart_count': cart.items_count,
                'cart_total': float(cart.total)
            })
        
        messages.success(request, 'Item removed from cart.')
        return redirect('orders:cart')


class CartClearView(CartMixin, View):
    """Clear entire cart."""

    def post(self, request):
        cart = self.get_cart(request)
        cart.clear()
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True, 'cart_count': 0, 'cart_total': 0})
        
        messages.success(request, 'Cart cleared.')
        return redirect('orders:cart')


class CheckoutView(CartMixin, View):
    """Checkout start - redirect to first step."""

    def get(self, request):
        cart = self.get_cart(request)
        if cart.items_count == 0:
            messages.warning(request, 'Your cart is empty.')
            return redirect('orders:cart')
        return redirect('orders:checkout_info')


class CheckoutInfoView(CartMixin, View):
    """Checkout step 1 - Customer info."""
    template_name = 'orders/checkout_info.html'

    def get(self, request):
        cart = self.get_cart(request)
        if cart.items_count == 0:
            return redirect('orders:cart')
        
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone': request.user.phone,
            }
        
        form = CheckoutForm(initial=initial)
        return render(request, self.template_name, {'form': form, 'cart': cart, 'step': 1})

    def post(self, request):
        cart = self.get_cart(request)
        form = CheckoutForm(request.POST)
        
        if form.is_valid():
            # Store in session
            request.session['checkout_info'] = form.cleaned_data
            return redirect('orders:checkout_shipping')
        
        return render(request, self.template_name, {'form': form, 'cart': cart, 'step': 1})


class CheckoutShippingView(CartMixin, View):
    """Checkout step 2 - Shipping address."""
    template_name = 'orders/checkout_shipping.html'

    def get(self, request):
        cart = self.get_cart(request)
        if cart.items_count == 0:
            return redirect('orders:cart')
        
        if 'checkout_info' not in request.session:
            return redirect('orders:checkout_info')
        
        initial = {}
        if request.user.is_authenticated:
            default_address = request.user.default_address
            if default_address:
                initial = {
                    'shipping_first_name': default_address.first_name,
                    'shipping_last_name': default_address.last_name,
                    'shipping_address': default_address.street_address,
                    'shipping_address_2': default_address.street_address_2,
                    'shipping_city': default_address.city,
                    'shipping_postal_code': default_address.postal_code,
                    'shipping_country': default_address.country,
                }
        
        form = ShippingForm(initial=initial)
        return render(request, self.template_name, {'form': form, 'cart': cart, 'step': 2})

    def post(self, request):
        cart = self.get_cart(request)
        form = ShippingForm(request.POST)
        
        if form.is_valid():
            request.session['checkout_shipping'] = form.cleaned_data
            return redirect('orders:checkout_payment')
        
        return render(request, self.template_name, {'form': form, 'cart': cart, 'step': 2})


class CheckoutPaymentView(CartMixin, View):
    """Checkout step 3 - Payment method selection."""
    template_name = 'orders/checkout_payment.html'

    def get(self, request):
        cart = self.get_cart(request)
        if cart.items_count == 0:
            return redirect('orders:cart')
        
        if 'checkout_shipping' not in request.session:
            return redirect('orders:checkout_shipping')
        
        return render(request, self.template_name, {'cart': cart, 'step': 3})

    def post(self, request):
        payment_method = request.POST.get('payment_method', 'ideal')
        request.session['checkout_payment'] = {'method': payment_method}
        return redirect('orders:checkout_confirm')


class CheckoutConfirmView(CartMixin, View):
    """Checkout step 4 - Review and confirm order."""
    template_name = 'orders/checkout_confirm.html'

    def get(self, request):
        cart = self.get_cart(request)
        if cart.items_count == 0:
            return redirect('orders:cart')
        
        checkout_info = request.session.get('checkout_info', {})
        checkout_shipping = request.session.get('checkout_shipping', {})
        checkout_payment = request.session.get('checkout_payment', {})
        
        if not all([checkout_info, checkout_shipping, checkout_payment]):
            return redirect('orders:checkout_info')
        
        context = {
            'cart': cart,
            'checkout_info': checkout_info,
            'checkout_shipping': checkout_shipping,
            'checkout_payment': checkout_payment,
            'step': 4,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        cart = self.get_cart(request)
        checkout_info = request.session.get('checkout_info', {})
        checkout_shipping = request.session.get('checkout_shipping', {})
        checkout_payment = request.session.get('checkout_payment', {})
        
        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            email=checkout_info.get('email'),
            phone=checkout_info.get('phone', ''),
            shipping_first_name=checkout_shipping.get('shipping_first_name'),
            shipping_last_name=checkout_shipping.get('shipping_last_name'),
            shipping_company=checkout_shipping.get('shipping_company', ''),
            shipping_address=checkout_shipping.get('shipping_address'),
            shipping_address_2=checkout_shipping.get('shipping_address_2', ''),
            shipping_city=checkout_shipping.get('shipping_city'),
            shipping_state=checkout_shipping.get('shipping_state', ''),
            shipping_postal_code=checkout_shipping.get('shipping_postal_code'),
            shipping_country=checkout_shipping.get('shipping_country', 'Netherlands'),
            subtotal=cart.subtotal,
            total=cart.total,
            payment_method=checkout_payment.get('method', 'ideal'),
            customer_notes=request.POST.get('notes', ''),
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                quantity=cart_item.quantity,
                price=cart_item.price,
                total=cart_item.total,
            )
        
        # Clear cart and session
        cart.clear()
        for key in ['checkout_info', 'checkout_shipping', 'checkout_payment']:
            request.session.pop(key, None)
        
        # Store order number for redirect
        request.session['pending_order'] = order.order_number

        # Send order confirmation email to customer
        from apps.notifications.tasks import send_order_confirmation_email, notify_admin_new_order
        try:
            send_order_confirmation_email(order.id)
            print(f"Order confirmation email sent for order {order.order_number}")
        except Exception as e:
            print(f"Failed to send order confirmation email: {e}")

        # Send admin notification email
        try:
            notify_admin_new_order(order.id)
            print(f"Admin notification email sent for order {order.order_number}")
        except Exception as e:
            print(f"Failed to send admin notification email: {e}")

        # For now, redirect directly to success page (mock payment)
        return redirect('orders:success', order_number=order.order_number)


class OrderSuccessView(View):
    """Order success page."""
    template_name = 'orders/order_success.html'

    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        return render(request, self.template_name, {'order': order})


class OrderFailedView(View):
    """Order payment failed page."""
    template_name = 'orders/order_failed.html'

    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        return render(request, self.template_name, {'order': order})

