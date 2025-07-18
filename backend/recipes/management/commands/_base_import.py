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
            rows = json.loads(self.data_path.read_text(encoding='utf-8'))
            to_create = [self.model(**row) for row in rows]
            created = self.model.objects.bulk_create(
                to_create, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(
                f'Импорт из {self.data_path.name} завершён: '
                f'добавлено {len(created)} '
                f'{self.model._meta.verbose_name_plural}'
            ))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(
                f'Ошибка при импорте из {self.data_path.name}: {exc}'
            ))
