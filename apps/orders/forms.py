from django import forms


class CheckoutForm(forms.Form):
    """Customer information form for checkout."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input',
            'placeholder': 'Email address',
        })
    )
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'First name',
        })
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Last name',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Phone number (optional)',
        })
    )
    create_account = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary-600 border-secondary-300 rounded focus:ring-primary-500',
        })
    )


class ShippingForm(forms.Form):
    """Shipping address form."""
    shipping_first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'First name',
        })
    )
    shipping_last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Last name',
        })
    )
    shipping_company = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Company (optional)',
        })
    )
    shipping_address = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Street address',
        })
    )
    shipping_address_2 = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Apartment, suite, etc. (optional)',
        })
    )
    shipping_city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'City',
        })
    )
    shipping_state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'State/Province (optional)',
        })
    )
    shipping_postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Postal code',
        })
    )
    shipping_country = forms.CharField(
        max_length=100,
        initial='Netherlands',
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Country',
        })
    )
    
    # Billing address option
    billing_same_as_shipping = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary-600 border-secondary-300 rounded focus:ring-primary-500',
        })
    )

