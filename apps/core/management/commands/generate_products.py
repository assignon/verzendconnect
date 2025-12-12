"""
Management command to generate 10 products with images for specific categories.
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from apps.core.models import Category, Product, ProductImage, EventType
from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
import io
import random


class Command(BaseCommand):
    help = 'Generate 10 products with images (2 per category)'

    def create_placeholder_image(self, width=800, height=600, color=(200, 200, 200), text=""):
        """Create a placeholder image."""
        img = Image.new('RGB', (width, height), color=color)
        
        # Add text if provided
        if text:
            try:
                draw = ImageDraw.Draw(img)
                # Try to use a default font
                try:
                    font = ImageFont.truetype("arial.ttf", 40)
                except:
                    try:
                        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)
                    except:
                        font = ImageFont.load_default()
                # Calculate text position (center)
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                position = ((width - text_width) // 2, (height - text_height) // 2)
                draw.text(position, text, fill=(100, 100, 100), font=font)
            except Exception as e:
                # If text rendering fails, just continue without text
                pass
        
        # Save to bytes
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        return ContentFile(img_io.read(), name=f'{text.replace(" ", "_").lower()}.jpg')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to generate products with images...'))

        # Get or create categories
        categories_map = {}
        category_names = [
            'Chairs',
            'Chairs with cushions',
            'Tables',
            'Carpet with posts',
            'Carpet'
        ]

        for cat_name in category_names:
            category, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={
                    'slug': cat_name.lower().replace(' ', '-'),
                    'description': f'{cat_name} for hire and partly for sale',
                    'is_active': True,
                }
            )
            categories_map[cat_name] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat_name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Found category: {cat_name}'))

        # Get some event types for assignment
        event_types = list(EventType.objects.filter(is_active=True)[:3])

        # Product data: 2 products per category
        products_data = [
            # Chairs (2 products)
            {
                'name': 'Classic Wooden Chair',
                'description': 'Elegant wooden chair perfect for any event. Comfortable and durable design. Available in various finishes.',
                'price': Decimal('25.00'),
                'sale_price': Decimal('20.00'),
                'stock': 50,
                'category': 'Chairs',
                'image_text': 'Wooden Chair'
            },
            {
                'name': 'Modern Plastic Chair',
                'description': 'Lightweight and stackable plastic chair. Easy to transport and clean. Perfect for outdoor events.',
                'price': Decimal('15.00'),
                'sale_price': None,
                'stock': 100,
                'category': 'Chairs',
                'image_text': 'Plastic Chair'
            },
            # Chairs with cushions (2 products)
            {
                'name': 'Luxury Cushioned Chair - White',
                'description': 'Comfortable chair with soft cushion. Elegant white fabric. Perfect for weddings and formal events.',
                'price': Decimal('35.00'),
                'sale_price': Decimal('30.00'),
                'stock': 40,
                'category': 'Chairs with cushions',
                'image_text': 'Cushioned Chair White'
            },
            {
                'name': 'Premium Cushioned Chair - Beige',
                'description': 'High-quality cushioned chair in elegant beige. Comfortable seating for long events.',
                'price': Decimal('40.00'),
                'sale_price': None,
                'stock': 35,
                'category': 'Chairs with cushions',
                'image_text': 'Cushioned Chair Beige'
            },
            # Tables (2 products)
            {
                'name': 'Round Table - 120cm',
                'description': 'Large round table perfect for dining. Seats 8-10 people. Sturdy construction.',
                'price': Decimal('45.00'),
                'sale_price': Decimal('40.00'),
                'stock': 30,
                'category': 'Tables',
                'image_text': 'Round Table'
            },
            {
                'name': 'Rectangular Table - 180cm',
                'description': 'Long rectangular table ideal for buffets and large gatherings. Easy to set up and clean.',
                'price': Decimal('50.00'),
                'sale_price': None,
                'stock': 25,
                'category': 'Tables',
                'image_text': 'Rectangular Table'
            },
            # Carpet with posts (2 products)
            {
                'name': 'Red Carpet with Posts - 10m',
                'description': 'Elegant red carpet with decorative posts. Perfect for entrances and walkways. Creates a grand entrance.',
                'price': Decimal('75.00'),
                'sale_price': Decimal('65.00'),
                'stock': 15,
                'category': 'Carpet with posts',
                'image_text': 'Red Carpet Posts'
            },
            {
                'name': 'Premium Carpet with Posts - 15m',
                'description': 'Luxury carpet with gold posts. Extra length for larger venues. Premium quality materials.',
                'price': Decimal('120.00'),
                'sale_price': None,
                'stock': 10,
                'category': 'Carpet with posts',
                'image_text': 'Premium Carpet Posts'
            },
            # Carpet (2 products)
            {
                'name': 'Event Carpet - 5m x 2m',
                'description': 'Versatile event carpet in neutral color. Perfect for covering floors and creating defined spaces.',
                'price': Decimal('30.00'),
                'sale_price': Decimal('25.00'),
                'stock': 20,
                'category': 'Carpet',
                'image_text': 'Event Carpet'
            },
            {
                'name': 'Premium Carpet - 8m x 3m',
                'description': 'Large premium carpet for spacious events. High-quality material, easy to clean and maintain.',
                'price': Decimal('55.00'),
                'sale_price': None,
                'stock': 12,
                'category': 'Carpet',
                'image_text': 'Premium Carpet'
            },
        ]

        created_count = 0
        for product_data in products_data:
            category = categories_map[product_data['category']]
            
            # Generate unique slug
            base_slug = slugify(product_data['name'])
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Create product
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
            
            # Assign event types
            if event_types:
                product.event_types.set(random.sample(event_types, k=min(random.randint(1, 3), len(event_types))))
            
            # Create product image
            image_file = self.create_placeholder_image(
                width=800,
                height=600,
                color=(220, 220, 220),
                text=product_data['image_text']
            )
            
            ProductImage.objects.create(
                product=product,
                image=image_file,
                alt_text=product_data['name'],
                is_primary=True,
                order=0
            )
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created product: {product.name} with image'))

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n{"="*50}'))
        self.stdout.write(self.style.SUCCESS('Product generation completed!'))
        self.stdout.write(self.style.SUCCESS(f'  Total Products Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Products with Images: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'{"="*50}'))

