# from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_order_confirmation_email(order_id):
    """Send order confirmation email to customer."""
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return False
    
    subject = f'Order Confirmation - {order.order_number}'
    html_message = render_to_string('notifications/emails/order_confirmation.html', {
        'order': order,
        'site_name': settings.SITE_NAME,
        'site_url': settings.SITE_URL,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        html_message=html_message,
    )
    
    # Log the email
    from .models import EmailLog
    EmailLog.objects.create(
        recipient=order.email,
        subject=subject,
        status='sent',
    )
    
    return True


def send_order_status_update_email(order_id):
    """Send order status update email to customer."""
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return False
    
    subject = f'Order Update - {order.order_number}'
    html_message = render_to_string('notifications/emails/order_status_update.html', {
        'order': order,
        'site_name': settings.SITE_NAME,
        'site_url': settings.SITE_URL,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        html_message=html_message,
    )
    
    return True


def send_verification_email(user_id):
    """Send email verification link to user."""
    from apps.accounts.models import CustomUser
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return False
    
    verification_url = f"{settings.SITE_URL}/accounts/verify-email/{user.email_verification_token}/"
    
    subject = f'Verify your email - {settings.SITE_NAME}'
    html_message = render_to_string('notifications/emails/email_verification.html', {
        'user': user,
        'verification_url': verification_url,
        'site_name': settings.SITE_NAME,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )
    
    return True


def notify_admin_new_order(order_id):
    """Send notification to admin when new order is placed."""
    from apps.orders.models import Order
    from apps.accounts.models import CustomUser
    from .models import Notification
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return False
    
    # Create in-app notification for all admin users
    admins = CustomUser.objects.filter(is_staff=True)
    for admin in admins:
        Notification.objects.create(
            recipient=admin,
            notification_type='new_order',
            title=f'New Order #{order.order_number}',
            message=f'A new order has been placed for €{order.total} by {order.email}',
            link=f'/admin/orders/order/{order.id}/change/',
            related_order_id=order.id,
        )
    
    # Send email to admin using ADMIN_EMAIL setting
    subject = f'New Order - {order.order_number}'
    html_message = render_to_string('notifications/emails/admin_new_order.html', {
        'order': order,
        'site_name': settings.SITE_NAME,
        'admin_url': f'{settings.SITE_URL}/admin/orders/order/{order.id}/change/',
    })
    plain_message = strip_tags(html_message)

    # Send email to the configured admin email
    admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@verzendconnect.nl')
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            html_message=html_message,
        )
        print(f"Admin notification email sent to: {admin_email}")
    except Exception as e:
        print(f"Failed to send admin notification email: {e}")
    
    return True


def send_payment_confirmation_email(order_id):
    """Send payment confirmation email."""
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return False
    
    subject = f'Payment Received - {order.order_number}'
    html_message = render_to_string('notifications/emails/payment_confirmation.html', {
        'order': order,
        'site_name': settings.SITE_NAME,
        'site_url': settings.SITE_URL,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        html_message=html_message,
    )
    
    return True

