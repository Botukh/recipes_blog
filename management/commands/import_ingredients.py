import csv
import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импортирует данные ингредиентов в таблицу Ingredient'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['csv', 'json'],
            default='csv',
            help='Укажите формат исходного файла. По умолчанию – csv.'
        )
        parser.add_argument(
            '--path',
            default='data/ingredients.csv',
            help='Путь до файла . По умолчанию: data/ingredients.csv'
        )

    def handle(self, *args, **options):
        file_format = options['format']
        path = options['path']
        full_path = os.path.join(os.getcwd(), path)

        if not os.path.isfile(full_path):
            raise CommandError(f"Файл не найден: {full_path}")

        with transaction.atomic():
            count = 0
            if file_format == 'csv':
                with open(full_path, encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    required_fields = {'name', 'measurement_unit'}
                    if not required_fields.issubset(reader.fieldnames):
                        raise CommandError()
                    for row in reader:
                        name = row['name'].strip()
                        unit = row['measurement_unit'].strip()
                        if not name:
                            continue
                        ing, created = Ingredient.objects.get_or_create(
                            name=name,
                            defaults={'measurement_unit': unit}
                        )
                        if not created:
                            ing.measurement_unit = unit
                            ing.save(update_fields=['measurement_unit'])
                        count += 1

            elif file_format == 'json':
                with open(full_path, encoding='utf-8') as jsonfile:
                    try:
                        data = json.load(jsonfile)
                    except json.JSONDecodeError as e:
                        raise CommandError(f"Ошибка при разборе JSON: {e}")

                    if not isinstance(data, list):
                        raise CommandError("JSON должен быть массивом")

                    for entry in data:
                        name = entry.get('name', '').strip()
                        unit = entry.get('measurement_unit', '').strip()
                        if not name:
                            continue
                        ing, created = Ingredient.objects.get_or_create(
                            name=name,
                            defaults={'measurement_unit': unit}
                        )
                        if not created:
                            ing.measurement_unit = unit
                            ing.save(update_fields=['measurement_unit'])
                        count += 1

            else:
                raise CommandError("Неподдерживаемый формат.")

            self.stdout.write(self.style.SUCCESS(
                f"Импортировано/обновлено {count} записей в Ingredient"
            ))
