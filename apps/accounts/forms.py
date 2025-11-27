from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Address


class LoginForm(forms.Form):
    """User login form."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input',
            'placeholder': 'Enter your email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'Enter your password',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary-600 border-secondary-300 rounded focus:ring-primary-500',
        })
    )


class RegisterForm(forms.ModelForm):
    """User registration form."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'Create a password',
        }),
        validators=[validate_password]
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'Confirm your password',
        })
    )
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary-600 border-secondary-300 rounded focus:ring-primary-500',
        })
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Last name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': 'Email address',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Phone number (optional)',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """User profile edit form."""
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'date_of_birth', 'avatar', 'newsletter_subscribed']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input'}),
            'last_name': forms.TextInput(attrs={'class': 'input'}),
            'phone': forms.TextInput(attrs={'class': 'input'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'avatar': forms.FileInput(attrs={'class': 'input'}),
            'newsletter_subscribed': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary-600 border-secondary-300 rounded focus:ring-primary-500',
            }),
        }


class PasswordChangeForm(DjangoPasswordChangeForm):
    """Custom password change form with styling."""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'Current password',
        })
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'New password',
        }),
        validators=[validate_password]
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'Confirm new password',
        })
    )


class AddressForm(forms.ModelForm):
    """Address form."""
    class Meta:
        model = Address
        fields = [
            'address_type', 'first_name', 'last_name', 'company', 'phone',
            'street_address', 'street_address_2', 'city', 'state', 'postal_code', 'country',
            'is_default'
        ]
        widgets = {
            'address_type': forms.Select(attrs={'class': 'input'}),
            'first_name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Last name'}),
            'company': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Company (optional)'}),
            'phone': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Phone number'}),
            'street_address': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Street address'}),
            'street_address_2': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Apartment, suite, etc. (optional)'}),
            'city': forms.TextInput(attrs={'class': 'input', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'input', 'placeholder': 'State/Province (optional)'}),
            'postal_code': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Postal code'}),
            'country': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Country'}),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary-600 border-secondary-300 rounded focus:ring-primary-500',
            }),
        }

