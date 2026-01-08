"""
Django management command to compile translation (.po) files to binary (.mo) files.
Uses polib library instead of GNU gettext tools.
"""
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

try:
    import polib
    HAS_POLIB = True
except ImportError:
    HAS_POLIB = False


class Command(BaseCommand):
    help = 'Compile translation .po files to .mo files using polib'

    def handle(self, *args, **options):
        if not HAS_POLIB:
            self.stderr.write(
                self.style.ERROR(
                    'polib is not installed. Install it with: pip install polib'
                )
            )
            return

        locale_paths = getattr(settings, 'LOCALE_PATHS', [])
        if not locale_paths:
            locale_paths = [Path(settings.BASE_DIR) / 'locale']

        compiled_count = 0
        error_count = 0

        for locale_path in locale_paths:
            locale_path = Path(locale_path)
            if not locale_path.exists():
                self.stdout.write(
                    self.style.WARNING(f'Locale path does not exist: {locale_path}')
                )
                continue

            # Find all .po files
            for po_file in locale_path.rglob('*.po'):
                mo_file = po_file.with_suffix('.mo')
                
                try:
                    self.stdout.write(f'Compiling {po_file}...')
                    po = polib.pofile(str(po_file))
                    po.save_as_mofile(str(mo_file))
                    compiled_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  -> Created {mo_file}')
                    )
                except Exception as e:
                    error_count += 1
                    self.stderr.write(
                        self.style.ERROR(f'  -> Error compiling {po_file}: {e}')
                    )

        self.stdout.write('')
        if compiled_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully compiled {compiled_count} translation file(s)'
                )
            )
        if error_count > 0:
            self.stderr.write(
                self.style.ERROR(f'Failed to compile {error_count} file(s)')
            )
        if compiled_count == 0 and error_count == 0:
            self.stdout.write(
                self.style.WARNING('No .po files found to compile')
            )

