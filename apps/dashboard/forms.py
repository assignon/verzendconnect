"""Forms for dashboard."""
from django import forms
from apps.core.models import SiteSettings


class CompanyInfoForm(forms.ModelForm):
    """Form for editing company contact information."""
    
    class Meta:
        model = SiteSettings
        fields = ['email', 'phone', 'address']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': 'contact@verzendconnect.nl'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': '+31 6 12345678'
            }),
            'address': forms.Textarea(attrs={
                'class': 'input',
                'rows': 4,
                'placeholder': 'Street Address\nCity, Postal Code\nCountry'
            }),
        }
        labels = {
            'email': 'Email Address',
            'phone': 'Phone Number',
            'address': 'Address',
        }
        help_texts = {
            'email': 'This email will be displayed in the footer and used for contact.',
            'phone': 'Phone number displayed in the footer. Include country code if needed.',
            'address': 'Full address displayed in the footer. Use line breaks for formatting.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional
        self.fields['email'].required = False
        self.fields['phone'].required = False
        self.fields['address'].required = False

