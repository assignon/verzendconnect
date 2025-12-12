#!/usr/bin/env python
import os
import django
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.forms import ProfileForm

# Get the admin user
User = get_user_model()
user = User.objects.filter(email='admin@verzendconnect.nl').first()
print(f'User: {user.email}')

# Test form initialization
form = ProfileForm(instance=user)
print(f'Form email field initial: {form.fields["email"].initial}')

# Test form validation with new email
test_data = {
    'first_name': user.first_name,
    'last_name': user.last_name,
    'email': 'newemail@test.com',
    'phone': user.phone or '',
    'date_of_birth': '',
    'newsletter_subscribed': False,
}

test_form = ProfileForm(data=test_data, instance=user)
print(f'Form is valid: {test_form.is_valid()}')
if not test_form.is_valid():
    print(f'Errors: {dict(test_form.errors)}')
else:
    print('Form validation successful!')
