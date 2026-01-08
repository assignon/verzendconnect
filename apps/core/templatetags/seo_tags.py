"""
SEO template tags for VerzendConnect.
"""
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from urllib.parse import urljoin
import json

register = template.Library()


@register.simple_tag
def absolute_url(path):
    """Generate absolute URL from a relative path."""
    site_url = getattr(settings, 'SITE_URL', 'https://verzendconnect.nl')
    return urljoin(site_url, path)


@register.simple_tag
def og_image(image_url=None, default_image='images/verzendconnectlogo.png'):
    """Generate absolute URL for Open Graph image."""
    site_url = getattr(settings, 'SITE_URL', 'https://verzendconnect.nl')
    if image_url:
        if image_url.startswith('http'):
            return image_url
        # Handle media files (they start with /media/)
        if image_url.startswith('/media/') or image_url.startswith('/static/'):
            return urljoin(site_url, image_url)
        # If it's a relative path, assume it's media
        if not image_url.startswith('/'):
            image_url = '/' + image_url
        return urljoin(site_url, image_url)
    return urljoin(site_url, f'/static/{default_image}')


@register.filter
def truncate_description(text, length=160):
    """Truncate text to specified length for meta descriptions."""
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'


@register.simple_tag
def json_ld(data):
    """Output JSON-LD structured data."""
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>')


@register.simple_tag
def breadcrumb_schema(items):
    """Generate breadcrumb schema.org structured data."""
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": []
    }
    
    for position, item in enumerate(items, start=1):
        schema["itemListElement"].append({
            "@type": "ListItem",
            "position": position,
            "name": item.get('name', ''),
            "item": item.get('url', '')
        })
    
    return json_ld(schema)


@register.simple_tag
def organization_schema():
    """Generate Organization schema.org structured data."""
    site_url = getattr(settings, 'SITE_URL', 'https://verzendconnect.nl')
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "VerzendConnect",
        "url": site_url,
        "logo": urljoin(site_url, '/static/images/verzendconnectlogo.png'),
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": "+31-610-652-556",
            "contactType": "Customer Service",
            "areaServed": "NL",
            "availableLanguage": ["en", "nl"]
        },
        "sameAs": [
            # Add social media URLs if available
        ]
    }
    
    return json_ld(schema)


@register.simple_tag
def product_schema(product):
    """Generate Product schema.org structured data."""
    site_url = getattr(settings, 'SITE_URL', 'https://verzendconnect.nl')
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": product.description or product.name,
        "image": [],
        "brand": {
            "@type": "Brand",
            "name": "VerzendConnect"
        },
        "offers": {
            "@type": "Offer",
            "url": urljoin(site_url, product.get_absolute_url()),
            "priceCurrency": "EUR",
            "price": str(product.sale_price if product.sale_price else product.price),
            "availability": "https://schema.org/InStock" if product.is_available and product.stock > 0 else "https://schema.org/OutOfStock",
            "priceValidUntil": "2025-12-31"
        },
        "category": product.category.name if product.category else None
    }
    
    # Add images
    if product.primary_image and product.primary_image.image:
        img_url = product.primary_image.image.url
        if not img_url.startswith('http'):
            img_url = urljoin(site_url, img_url)
        schema["image"].append(img_url)
    
    for img in product.images.all()[:5]:
        if img.image:
            img_url = img.image.url
            if not img_url.startswith('http'):
                img_url = urljoin(site_url, img_url)
            schema["image"].append(img_url)
    
    if not schema["image"]:
        schema["image"].append(urljoin(site_url, '/static/images/verzendconnectlogo.png'))
    
    # Remove None values
    schema = {k: v for k, v in schema.items() if v is not None}
    
    return json_ld(schema)


@register.simple_tag
def local_business_schema():
    """Generate LocalBusiness schema.org structured data for local SEO."""
    site_url = getattr(settings, 'SITE_URL', 'https://verzendconnect.nl')
    
    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "VerzendConnect",
        "image": urljoin(site_url, '/static/images/verzendconnectlogo.png'),
        "url": site_url,
        "telephone": "+31-610-652-556",
        "priceRange": "€€",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Amsterdam",
            "addressRegion": "North Holland",
            "addressCountry": "NL"
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": 52.3676,
            "longitude": 4.9041
        },
        "openingHoursSpecification": {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday"
            ],
            "opens": "09:00",
            "closes": "18:00"
        },
        "areaServed": {
            "@type": "Country",
            "name": "Netherlands"
        }
    }
    
    return json_ld(schema)


@register.simple_tag
def website_schema():
    """Generate WebSite schema.org structured data."""
    site_url = getattr(settings, 'SITE_URL', 'https://verzendconnect.nl')
    
    schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "VerzendConnect",
        "url": site_url,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": urljoin(site_url, "/search/?q={search_term_string}")
            },
            "query-input": "required name=search_term_string"
        }
    }
    
    return json_ld(schema)

