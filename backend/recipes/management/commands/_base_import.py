import json
from pathlib import Path
from typing import Type

from django.core.management.base import BaseCommand
from django.db.models import Model


class BaseImportCommand(BaseCommand):
    model: Type[Model]
    data_path: Path

    def handle(self, *args, **kwargs):
        try:
            data = json.loads(self.data_path.read_text(encoding='utf-8'))
            existing = set(
                self.model.objects.values_list('name', 'unit')
            )
            objects = [
                self.model(**row)
                for row in data
                if (row['name'], row['amount_unit']) not in existing
            ]
            self.model.objects.bulk_create(objects)
            self.stdout.write(self.style.SUCCESS(
                f'Импорт из {self.data_path.name} завершён: '
                f'добавлено {len(objects)}'
                f'{self.model._meta.verbose_name_plural}'
            ))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(
                f'Ошибка при импорте из {self.data_path.name}: {exc}'
            ))
