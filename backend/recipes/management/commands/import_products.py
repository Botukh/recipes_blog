import json
import pathlib
from django.core.management.base import BaseCommand
from django.db import transaction
from recipes.models import Product

DATA_PATH = pathlib.Path('data/products.json')


class Command(BaseCommand):
    help = 'Импорт продуктов из data/products.json (bulk_create)'

    def handle(self, *args, **kwargs):
        try:
            data = json.loads(DATA_PATH.read_text(encoding='utf-8'))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'Ошибка чтения файла: {exc}'))
            return

        objects = [
            Product(
                name=row['name'].strip(), unit=row['measurement_unit'].strip())
            for row in data if row.get('name')
        ]

        with transaction.atomic():
            Product.objects.all().delete()
            Product.objects.bulk_create(objects, batch_size=5000)

        self.stdout.write(
            self.style.SUCCESS(f'Импортировано {len(objects)} продуктов')
        )
