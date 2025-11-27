from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from .models import CustomUser, Address


class AddressInline(TabularInline):
    model = Address
    extra = 0
    fields = ['address_type', 'first_name', 'last_name', 'street_address', 'city', 'postal_code', 'is_default']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'email_verified', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'email_verified', 'newsletter_subscribed']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    inlines = [AddressInline]
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'username', 'phone', 'date_of_birth', 'avatar')}),
        ('Verification', {'fields': ('email_verified', 'email_verification_token')}),
        ('Preferences', {'fields': ('newsletter_subscribed',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ['user', 'address_type', 'full_name', 'city', 'country', 'is_default']
    list_filter = ['address_type', 'country', 'is_default']
    search_fields = ['user__email', 'first_name', 'last_name', 'city']

