"""
Management command to populate Category and EventType tables from JSON files.
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.core.models import EventType, Category


class Command(BaseCommand):
    help = 'Load categories and event types from JSON files in apps/core/setup/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories and event types before loading',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to load setup data from JSON files...'))

        # Get the base directory (go up from management/commands/load_setup_data.py to project root)
        # Path structure: project_root/apps/core/management/commands/load_setup_data.py
        # We need: project_root/apps/core/setup/
        command_file = Path(__file__).resolve()
        setup_dir = command_file.parent.parent.parent / 'setup'

        # Load Event Types
        event_json_path = setup_dir / 'event.json'
        if event_json_path.exists():
            self.stdout.write(self.style.SUCCESS(f'\nLoading event types from {event_json_path}...'))
            
            if options['clear']:
                deleted_count = EventType.objects.count()
                EventType.objects.all().delete()
                self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing event types'))
            
            with open(event_json_path, 'r', encoding='utf-8') as f:
                event_data = json.load(f)
            
            created_count = 0
            updated_count = 0
            for i, event_info in enumerate(event_data):
                event_type, created = EventType.objects.get_or_create(
                    slug=event_info.get('slug', ''),
                    defaults={
                        'name': event_info.get('name', ''),
                        'description': event_info.get('description', ''),
                        'is_active': True,
                        'order': i,
                    }
                )
                
                if not created:
                    # Update existing event type
                    event_type.name = event_info.get('name', event_type.name)
                    event_type.description = event_info.get('description', event_type.description)
                    event_type.order = i
                    event_type.is_active = True
                    event_type.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Updated event type: {event_type.name}'))
                else:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created event type: {event_type.name}'))
            
            self.stdout.write(self.style.SUCCESS(f'\nEvent Types: {created_count} created, {updated_count} updated'))
        else:
            self.stdout.write(self.style.ERROR(f'Event JSON file not found at {event_json_path}'))

        # Load Categories
        category_json_path = setup_dir / 'category.json'
        if category_json_path.exists():
            self.stdout.write(self.style.SUCCESS(f'\nLoading categories from {category_json_path}...'))
            
            if options['clear']:
                deleted_count = Category.objects.count()
                Category.objects.all().delete()
                self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing categories'))
            
            with open(category_json_path, 'r', encoding='utf-8') as f:
                category_data = json.load(f)
            
            created_count = 0
            updated_count = 0
            for i, category_info in enumerate(category_data):
                category, created = Category.objects.get_or_create(
                    slug=category_info.get('slug', ''),
                    defaults={
                        'name': category_info.get('name', ''),
                        'description': category_info.get('description', ''),
                        'is_active': True,
                        'is_featured': i < 3,  # First 3 are featured
                        'order': i,
                    }
                )
                
                if not created:
                    # Update existing category
                    category.name = category_info.get('name', category.name)
                    category.description = category_info.get('description', category.description)
                    category.order = i
                    category.is_active = True
                    category.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Updated category: {category.name}'))
                else:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created category: {category.name}'))
                
                # Note: Image field is optional and would need to be handled separately
                # if image files are provided in a media directory
                if category_info.get('image'):
                    self.stdout.write(self.style.WARNING(
                        f'  Note: Image "{category_info.get("image")}" specified but not automatically loaded. '
                        f'Upload manually through admin or use file path.'
                    ))
            
            self.stdout.write(self.style.SUCCESS(f'\nCategories: {created_count} created, {updated_count} updated'))
        else:
            self.stdout.write(self.style.ERROR(f'Category JSON file not found at {category_json_path}'))

        # Summary
        total_events = EventType.objects.count()
        total_categories = Category.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*50}'))
        self.stdout.write(self.style.SUCCESS('Setup data loading completed!'))
        self.stdout.write(self.style.SUCCESS(f'  Total Event Types: {total_events}'))
        self.stdout.write(self.style.SUCCESS(f'  Total Categories: {total_categories}'))
        self.stdout.write(self.style.SUCCESS(f'{"="*50}'))

