from .models import Cart


def cart_context(request):
    """Add cart data to all templates."""
    cart = None
    cart_count = 0
    cart_total = 0
    
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    elif request.session.session_key:
        cart = Cart.objects.filter(session_key=request.session.session_key).first()
    
    if cart:
        cart_count = cart.items_count
        cart_total = cart.total
    
    return {
        'cart': cart,
        'cart_count': cart_count,
        'cart_total': cart_total,
    }

