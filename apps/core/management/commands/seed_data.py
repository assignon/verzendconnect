"""
Management command to seed the database with sample data for testing.
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.core.models import EventType, Category, Product, ProductImage, SiteSettings
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Seed the database with sample products, categories, and event types'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))

        # Create Event Types
        event_types_data = [
            {'name': 'Wedding', 'description': 'Everything you need for your perfect wedding day', 'icon': 'favorite'},
            {'name': 'Birthday', 'description': 'Celebrate birthdays in style', 'icon': 'cake'},
            {'name': 'Corporate', 'description': 'Professional events and corporate gatherings', 'icon': 'business'},
            {'name': 'Anniversary', 'description': 'Celebrate special milestones', 'icon': 'celebration'},
            {'name': 'Baby Shower', 'description': 'Welcome the little one', 'icon': 'child_care'},
        ]

        event_types = []
        for i, data in enumerate(event_types_data):
            event_type, created = EventType.objects.get_or_create(
                slug=data['name'].lower().replace(' ', '-'),
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'icon': data['icon'],
                    'is_active': True,
                    'order': i,
                }
            )
            event_types.append(event_type)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created event type: {event_type.name}'))

        # Create Categories
        categories_data = [
            {'name': 'Cakes', 'description': 'Delicious cakes for every occasion'},
            {'name': 'Decorations', 'description': 'Beautiful decorations to transform your space'},
            {'name': 'Catering', 'description': 'Professional catering services'},
            {'name': 'DJ Services', 'description': 'Music and entertainment'},
            {'name': 'Photography', 'description': 'Capture your special moments'},
            {'name': 'Flowers', 'description': 'Fresh flowers and arrangements'},
        ]

        categories = []
        for i, data in enumerate(categories_data):
            category, created = Category.objects.get_or_create(
                slug=data['name'].lower().replace(' ', '-'),
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'is_active': True,
                    'is_featured': i < 3,  # First 3 are featured
                    'order': i,
                }
            )
            # Assign random event types to categories
            category.event_types.set(random.sample(event_types, k=random.randint(2, 4)))
            categories.append(category)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))

        # Create Products
        products_data = [
            {
                'name': 'Elegant Wedding Cake - 3 Tiers',
                'description': 'A stunning 3-tier wedding cake decorated with fresh flowers and elegant frosting. Perfect for 50-80 guests. Available in vanilla, chocolate, or red velvet.',
                'price': Decimal('450.00'),
                'sale_price': None,
                'stock': 5,
                'category': 'Cakes',
            },
            {
                'name': 'Birthday Party Balloon Arch',
                'description': 'Colorful balloon arch perfect for birthday celebrations. Customizable colors. Includes installation.',
                'price': Decimal('120.00'),
                'sale_price': Decimal('99.00'),
                'stock': 10,
                'category': 'Decorations',
            },
            {
                'name': 'Premium Catering Package - 50 People',
                'description': 'Complete catering service for 50 guests. Includes appetizers, main course, desserts, and beverages. Professional service staff included.',
                'price': Decimal('2500.00'),
                'sale_price': None,
                'stock': 3,
                'category': 'Catering',
            },
            {
                'name': 'Professional DJ Service - 4 Hours',
                'description': 'Experienced DJ with professional sound system. Includes lighting, microphone, and music library. Perfect for weddings and parties.',
                'price': Decimal('600.00'),
                'sale_price': Decimal('550.00'),
                'stock': 8,
                'category': 'DJ Services',
            },
            {
                'name': 'Wedding Photography Package',
                'description': 'Full-day wedding photography coverage. Includes engagement shoot, ceremony, reception, and edited digital photos. Professional photographer.',
                'price': Decimal('1800.00'),
                'sale_price': None,
                'stock': 4,
                'category': 'Photography',
            },
            {
                'name': 'Bridal Bouquet - Premium',
                'description': 'Luxurious bridal bouquet with premium roses, peonies, and eucalyptus. Hand-tied with silk ribbon. Available in various color schemes.',
                'price': Decimal('180.00'),
                'sale_price': Decimal('150.00'),
                'stock': 12,
                'category': 'Flowers',
            },
            {
                'name': 'Corporate Event Catering - 30 People',
                'description': 'Professional catering for corporate events. Includes coffee break, lunch buffet, and refreshments. Business-appropriate menu.',
                'price': Decimal('1200.00'),
                'sale_price': None,
                'stock': 6,
                'category': 'Catering',
            },
            {
                'name': 'Kids Birthday Party Decoration Set',
                'description': 'Complete decoration package for children\'s birthday parties. Includes banners, balloons, tableware, and party favors. Theme options available.',
                'price': Decimal('85.00'),
                'sale_price': Decimal('70.00'),
                'stock': 15,
                'category': 'Decorations',
            },
            {
                'name': 'Anniversary Cake - 2 Tiers',
                'description': 'Elegant anniversary cake for couples celebrating their special day. Customizable with names and dates. Available in various flavors.',
                'price': Decimal('280.00'),
                'sale_price': None,
                'stock': 7,
                'category': 'Cakes',
            },
            {
                'name': 'Baby Shower Floral Centerpiece',
                'description': 'Beautiful floral centerpiece for baby shower tables. Includes seasonal flowers in pastel colors. Perfect for decorating the celebration space.',
                'price': Decimal('95.00'),
                'sale_price': Decimal('80.00'),
                'stock': 10,
                'category': 'Flowers',
            },
        ]

        # Delete existing products if they exist
        existing_count = Product.objects.count()
        if existing_count > 0:
            self.stdout.write(self.style.WARNING(f'Deleting {existing_count} existing products...'))
            Product.objects.all().delete()
        
        created_count = 0
        for product_data in products_data:
            category = next(c for c in categories if c.name == product_data['category'])
            
            # Generate unique slug
            base_slug = product_data['name'].lower().replace(' ', '-').replace("'", '').replace(',', '').replace('---', '-')
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            product = Product.objects.create(
                name=product_data['name'],
                slug=slug,
                description=product_data['description'],
                short_description=product_data['description'][:297] + '...' if len(product_data['description']) > 300 else product_data['description'],
                price=product_data['price'],
                sale_price=product_data['sale_price'],
                category=category,
                stock=product_data['stock'],
                is_available=True,
                is_active=True,
                is_featured=created_count < 4,  # First 4 are featured
            )
            
            # Assign random event types
            product.event_types.set(random.sample(event_types, k=random.randint(1, 3)))
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))
        
        # Create Site Settings if they don't exist
        settings, created = SiteSettings.objects.get_or_create(
            pk=1,
            defaults={
                'site_name': 'VerzendConnect',
                'site_tagline': 'Your one-stop shop for everything events. Making your celebrations unforgettable.',
                'email': 'info@verzendconnect.nl',
                'phone': '+31 20 123 4567',
                'address': 'Amsterdam, Netherlands',
                'currency': 'EUR',
                'currency_symbol': '€',
                'meta_title': 'VerzendConnect - Event Ordering Platform',
                'meta_description': 'Order everything you need for your perfect event - birthdays, weddings, and private parties.',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created site settings'))

        self.stdout.write(self.style.SUCCESS(f'\nDatabase seeding completed!'))
        self.stdout.write(self.style.SUCCESS(f'   - {len(event_types)} Event Types'))
        self.stdout.write(self.style.SUCCESS(f'   - {len(categories)} Categories'))
        self.stdout.write(self.style.SUCCESS(f'   - {created_count} Products'))
        self.stdout.write(self.style.SUCCESS('\nYou can now test the application with sample data!'))

