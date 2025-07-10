import json
import pathlib

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from recipes.models import Ingredient

DATA_PATH = pathlib.Path('data/ingredients.json')


class Command(BaseCommand):
    help = 'Импорт ингредиентов из data/ingredients.json (bulk_create)'

    def handle(self, *args, **kwargs):

        if 'recipes_ingredient' not in connection.introspection.table_names():
            self.stdout.write(self.style.WARNING(
                'Таблица recipes_ingredient не найдена. Пропускаю импорт.'))
            return

        try:
            data = json.loads(DATA_PATH.read_text(encoding='utf-8'))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'Ошибка чтения файла: {exc}'))
            return

        objects = [
            Ingredient(
                name=row['name'].strip(),
                unit=row['measurement_unit'].strip()
            )
            for row in data if row.get('name')
        ]

        with transaction.atomic():
            Ingredient.objects.all().delete()
            Ingredient.objects.bulk_create(objects, batch_size=5000)

        self.stdout.write(
            self.style.SUCCESS(f'✅ Импортировано {len(objects)} ингредиентов')
        )
