"""
Management command to populate FAQ and Rental Terms & Conditions.
"""
from django.core.management.base import BaseCommand
from apps.core.models import FAQ, RentalTerms


class Command(BaseCommand):
    help = 'Populate FAQ and Rental Terms & Conditions with default content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-faq',
            action='store_true',
            help='Clear existing FAQs before adding new ones',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate FAQ and Rental Terms...'))

        # Clear existing FAQs if requested
        if options['clear_faq']:
            FAQ.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing FAQs'))

        # Create FAQs
        faqs_data = [
            {
                'question': 'How far in advance should I book my rental items?',
                'answer': 'We recommend booking at least 2 days in advance to ensure availability. For popular items during peak seasons (wedding season, holidays), we suggest booking 1-2 weeks ahead. You can check availability in real-time on our website when selecting your rental dates.',
                'order': 1,
            },
            {
                'question': 'What is the minimum rental period?',
                'answer': 'The minimum rental period is typically 1 day. However, some items may have different minimum rental periods. Please check the product details for specific information. Rental periods are calculated from the start date to the return date you select during checkout.',
                'order': 2,
            },
            {
                'question': 'How do I know if an item is available for my event dates?',
                'answer': 'When you add items to your cart and proceed to checkout, you will be asked to select rental start and end dates. Our system automatically checks availability based on existing rentals and stock levels. If an item is not available for your selected dates, you will be notified before completing your order.',
                'order': 3,
            },
            {
                'question': 'What happens if I return items late?',
                'answer': 'Items must be returned by the specified return date. If items are returned more than 2 days late, you may be charged additional rental fees. We will send reminders as the return date approaches. For extended delays, please contact us immediately to discuss options.',
                'order': 4,
            },
            {
                'question': 'Can I cancel or modify my order?',
                'answer': 'Yes, you can cancel or modify your order before the rental start date. Please contact us as soon as possible. Cancellations made less than 48 hours before the rental start date may be subject to a cancellation fee. Modifications are subject to item availability.',
                'order': 5,
            },
            {
                'question': 'What payment methods do you accept?',
                'answer': 'We accept payments through Mollie, which supports iDEAL, PayPal, credit cards, and other popular payment methods. Payment is required at the time of order confirmation. You will be redirected to a secure payment page to complete your transaction.',
                'order': 6,
            },
            {
                'question': 'Do you offer delivery and pickup services?',
                'answer': 'Yes, we offer delivery and pickup services. Delivery and pickup options, along with associated fees, will be displayed during checkout. Please ensure someone is available to receive the items on the delivery date and to be present for pickup on the return date.',
                'order': 7,
            },
            {
                'question': 'What condition should items be in when I return them?',
                'answer': 'Items should be returned in the same condition as received, normal wear and tear excepted. Please clean items if necessary (especially tables and chairs). Any damage beyond normal wear and tear may result in repair or replacement charges. We will inspect items upon return.',
                'order': 8,
            },
            {
                'question': 'What if an item is damaged or missing when I receive it?',
                'answer': 'Please inspect all items immediately upon delivery or pickup. If you notice any damage or missing items, contact us within 24 hours. We will arrange for replacements or provide appropriate compensation. Taking photos of any issues is recommended.',
                'order': 9,
            },
            {
                'question': 'Do you provide setup and breakdown services?',
                'answer': 'Yes, we offer setup and breakdown services for an additional fee. This service can be selected during checkout. Our team will set up items at your event location and return to break them down after your event. Please discuss specific requirements with us.',
                'order': 10,
            },
            {
                'question': 'Can I rent items for events outside of Amsterdam?',
                'answer': 'Yes, we serve events throughout the Netherlands. Delivery fees may vary based on location and distance. Please enter your event location during checkout to see delivery options and pricing. For events far from Amsterdam, additional travel fees may apply.',
                'order': 11,
            },
            {
                'question': 'What happens if my event is cancelled due to weather or other circumstances?',
                'answer': 'If you need to cancel due to unforeseen circumstances, please contact us immediately. We will work with you to reschedule or provide a refund based on our cancellation policy. Weather-related cancellations are handled on a case-by-case basis.',
                'order': 12,
            },
        ]

        created_count = 0
        for faq_data in faqs_data:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults={
                    'answer': faq_data['answer'],
                    'order': faq_data['order'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created FAQ: {faq.question[:50]}...'))
            else:
                self.stdout.write(self.style.WARNING(f'FAQ already exists: {faq.question[:50]}...'))

        self.stdout.write(self.style.SUCCESS(f'\nCreated {created_count} new FAQs'))

        # Create or update Rental Terms & Conditions
        rental_terms_content = """<h2>1. General Terms</h2>
<p>These Rental Terms and Conditions ("Terms") govern the rental of products and equipment from VerzendConnect ("we," "us," or "our"). By placing an order, you ("Customer," "you," or "your") agree to be bound by these Terms.</p>

<h2>2. Rental Period</h2>
<p>The rental period begins on the start date specified in your order and ends on the return date specified. The minimum rental period is typically 1 day, unless otherwise specified for specific items.</p>
<p>You must return all items by the specified return date. Late returns may result in additional charges as outlined in Section 6.</p>

<h2>3. Booking and Payment</h2>
<p>All bookings are subject to availability. We recommend booking at least 2 days in advance, especially during peak seasons.</p>
<p>Payment is required at the time of order confirmation. We accept payments through Mollie, supporting iDEAL, PayPal, credit cards, and other methods.</p>
<p>Prices are in Euros (€) and include VAT unless otherwise stated. Delivery, pickup, setup, and breakdown services may incur additional fees.</p>

<h2>4. Availability and Stock</h2>
<p>We reserve the right to substitute items of equal or better quality if the requested items are unavailable. If no suitable substitute is available, we will provide a full refund for the unavailable items.</p>
<p>Our system automatically checks stock availability based on your selected rental dates. If items become unavailable after your order is confirmed, we will contact you immediately.</p>

<h2>5. Delivery and Pickup</h2>
<p>Delivery and pickup dates and times will be confirmed with you after order placement. You must ensure someone is available to receive items on the delivery date and to be present for pickup on the return date.</p>
<p>If you are unavailable at the scheduled time, additional fees may apply for rescheduling.</p>
<p>You are responsible for providing accurate delivery addresses and access instructions. We are not liable for delays caused by incorrect information or inaccessible locations.</p>

<h2>6. Late Returns and Additional Charges</h2>
<p>Items must be returned by the specified return date. If items are returned more than 2 days late, you will be charged:</p>
<ul>
<li>An additional daily rental fee for each day beyond the return date</li>
<li>Any costs incurred due to the late return affecting other customers' bookings</li>
</ul>
<p>We will send email reminders as the return date approaches. For extended delays, please contact us immediately.</p>

<h2>7. Condition of Items</h2>
<p>All items are inspected before delivery. You should inspect items immediately upon receipt and report any damage or missing items within 24 hours.</p>
<p>Items must be returned in the same condition as received, normal wear and tear excepted. You are responsible for cleaning items if necessary (especially tables, chairs, and carpets).</p>
<p>Any damage beyond normal wear and tear will result in repair or replacement charges. We will assess the condition of items upon return.</p>

<h2>8. Damage and Loss</h2>
<p>You are responsible for all items from the time of delivery until return. This includes:</p>
<ul>
<li>Loss or theft of items</li>
<li>Damage caused by misuse, negligence, or accidents</li>
<li>Damage from weather exposure (if items are left outside without protection)</li>
</ul>
<p>Charges for damage or loss will be based on repair costs or replacement value. We will provide an itemized invoice for any charges.</p>

<h2>9. Cancellation and Modifications</h2>
<p>You may cancel or modify your order before the rental start date. Cancellations made:</p>
<ul>
<li>More than 48 hours before the start date: Full refund</li>
<li>Less than 48 hours before the start date: 50% refund or credit toward future rental</li>
<li>On or after the start date: No refund</li>
</ul>
<p>Modifications are subject to item availability and may incur additional fees if prices have changed.</p>
<p>We reserve the right to cancel orders due to circumstances beyond our control (e.g., severe weather, supplier issues). In such cases, you will receive a full refund.</p>

<h2>10. Use of Items</h2>
<p>Items must be used only for their intended purpose and in accordance with any provided instructions. You may not:</p>
<ul>
<li>Modify, alter, or repair items without our written consent</li>
<li>Sublet or transfer items to third parties</li>
<li>Use items in a manner that violates any laws or regulations</li>
</ul>

<h2>11. Liability</h2>
<p>We are not liable for any indirect, incidental, or consequential damages arising from the use of rented items, including but not limited to:</p>
<ul>
<li>Personal injury or property damage</li>
<li>Loss of profits or business interruption</li>
<li>Event cancellation or disruption</li>
</ul>
<p>Our total liability is limited to the rental fee paid for the specific items in question.</p>
<p>You are responsible for ensuring that items are used safely and appropriately. We recommend obtaining appropriate insurance for your event.</p>

<h2>12. Force Majeure</h2>
<p>We are not liable for delays or failures to perform due to circumstances beyond our reasonable control, including but not limited to:</p>
<ul>
<li>Natural disasters, severe weather, or acts of God</li>
<li>War, terrorism, or civil unrest</li>
<li>Strikes, labor disputes, or supplier failures</li>
<li>Government actions or regulations</li>
<li>Pandemics or health emergencies</li>
</ul>
<p>In such cases, we will work with you to find alternative solutions or provide appropriate refunds.</p>

<h2>13. Privacy and Data Protection</h2>
<p>We collect and process your personal data in accordance with our Privacy Policy and applicable data protection laws. Your information is used to process orders, communicate with you, and improve our services.</p>

<h2>14. Disputes and Governing Law</h2>
<p>These Terms are governed by Dutch law. Any disputes will be subject to the exclusive jurisdiction of the courts of Amsterdam, Netherlands.</p>
<p>If you have any concerns or disputes, please contact us first. We are committed to resolving issues fairly and promptly.</p>

<h2>15. Contact Information</h2>
<p>For questions, concerns, or support regarding your rental:</p>
<ul>
<li>Email: support@verzendconnect.nl</li>
<li>Phone: +31 6 10 65 25 56</li>
<li>Address: Amsterdam, Netherlands</li>
</ul>

<h2>16. Changes to Terms</h2>
<p>We reserve the right to modify these Terms at any time. Changes will be effective immediately upon posting on our website. Your continued use of our services after changes are posted constitutes acceptance of the modified Terms.</p>
<p>These Terms were last updated on the date shown at the top of this page.</p>

<p><strong>By placing an order, you acknowledge that you have read, understood, and agree to be bound by these Rental Terms and Conditions.</strong></p>"""

        rental_terms, created = RentalTerms.objects.get_or_create(
            pk=1,
            defaults={
                'title': 'Rental Terms and Conditions',
                'content': rental_terms_content,
                'is_active': True,
            }
        )
        if not created:
            # Update existing terms
            rental_terms.content = rental_terms_content
            rental_terms.is_active = True
            rental_terms.save()
            self.stdout.write(self.style.SUCCESS('Updated Rental Terms & Conditions'))
        else:
            self.stdout.write(self.style.SUCCESS('Created Rental Terms & Conditions'))

        self.stdout.write(self.style.SUCCESS('\n✓ FAQ and Rental Terms population completed!'))
        self.stdout.write(self.style.SUCCESS(f'   - {FAQ.objects.count()} total FAQs'))
        self.stdout.write(self.style.SUCCESS('   - Rental Terms & Conditions ready'))

