import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    PasswordResetView as DjangoPasswordResetView,
    PasswordResetDoneView as DjangoPasswordResetDoneView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
    PasswordResetCompleteView as DjangoPasswordResetCompleteView,
)
from django.contrib import messages
from django.urls import reverse_lazy
from .models import CustomUser, Address
from .forms import (
    LoginForm, RegisterForm, ProfileForm, PasswordChangeForm, AddressForm
)
from apps.orders.models import Order, Cart


class LoginView(View):
    """User login view."""
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:home')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                # Merge guest cart if exists
                session_key = request.session.session_key
                if session_key:
                    guest_cart = Cart.objects.filter(session_key=session_key).first()
                    if guest_cart:
                        user_cart, created = Cart.objects.get_or_create(user=user)
                        if not created:
                            user_cart.merge_with(guest_cart)
                        else:
                            guest_cart.user = user
                            guest_cart.session_key = None
                            guest_cart.save()
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.email}!')
                
                next_url = request.GET.get('next', 'core:home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password.')
        
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """User logout view."""
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('core:home')


class RegisterView(View):
    """User registration view."""
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:home')
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email  # Use email as username
            user.email_verification_token = str(uuid.uuid4())
            user.save()
            
            # TODO: Send verification email via Celery task
            
            messages.success(request, 'Account created successfully! Please check your email to verify your account.')
            return redirect('accounts:login')
        
        return render(request, self.template_name, {'form': form})


class VerifyEmailView(View):
    """Email verification view."""
    def get(self, request, token):
        user = get_object_or_404(CustomUser, email_verification_token=token)
        user.email_verified = True
        user.email_verification_token = ''
        user.save()
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('accounts:login')


class ResendVerificationView(LoginRequiredMixin, View):
    """Resend verification email."""
    def post(self, request):
        if request.user.email_verified:
            messages.info(request, 'Your email is already verified.')
        else:
            request.user.email_verification_token = str(uuid.uuid4())
            request.user.save()
            # TODO: Send verification email via Celery task
            messages.success(request, 'Verification email sent!')
        return redirect('accounts:profile')


class PasswordResetView(DjangoPasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/emails/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class PasswordResetDoneView(DjangoPasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class PasswordResetConfirmView(DjangoPasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class PasswordResetCompleteView(DjangoPasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view."""
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_orders'] = Order.objects.filter(user=self.request.user)[:5]
        context['addresses'] = Address.objects.filter(user=self.request.user)
        return context


class ProfileEditView(LoginRequiredMixin, View):
    """Edit user profile."""
    template_name = 'accounts/profile_edit.html'

    def get(self, request):
        form = ProfileForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form})


class PasswordChangeView(LoginRequiredMixin, View):
    """Change password view."""
    template_name = 'accounts/password_change.html'

    def get(self, request):
        form = PasswordChangeForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form})


class AddressListView(LoginRequiredMixin, ListView):
    """List user addresses."""
    template_name = 'accounts/address_list.html'
    context_object_name = 'addresses'

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressCreateView(LoginRequiredMixin, View):
    """Create new address."""
    template_name = 'accounts/address_form.html'

    def get(self, request):
        form = AddressForm()
        return render(request, self.template_name, {'form': form, 'title': 'Add Address'})

    def post(self, request):
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('accounts:address_list')
        return render(request, self.template_name, {'form': form, 'title': 'Add Address'})


class AddressEditView(LoginRequiredMixin, View):
    """Edit address."""
    template_name = 'accounts/address_form.html'

    def get(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        form = AddressForm(instance=address)
        return render(request, self.template_name, {'form': form, 'title': 'Edit Address'})

    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('accounts:address_list')
        return render(request, self.template_name, {'form': form, 'title': 'Edit Address'})


class AddressDeleteView(LoginRequiredMixin, View):
    """Delete address."""
    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        address.delete()
        messages.success(request, 'Address deleted successfully!')
        return redirect('accounts:address_list')


class OrderHistoryView(LoginRequiredMixin, ListView):
    """List user orders."""
    template_name = 'accounts/order_history.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderDetailView(LoginRequiredMixin, View):
    """Order detail view."""
    template_name = 'accounts/order_detail.html'

    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        return render(request, self.template_name, {'order': order})

