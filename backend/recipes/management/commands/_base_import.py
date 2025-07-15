import json
from pathlib import Path
from typing import Type

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Model


class BaseImportCommand(BaseCommand):
    model: Type[Model]
    data_path: Path
    verbose_model_name = 'данные'

    def handle(self, *args, **kwargs):
        try:
            with self.data_path.open(encoding='utf-8') as file:
                data = json.load(file)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(
                f'Ошибка чтения файла {self.data_path.name}: {exc}'
            ))
            return

        try:
            with transaction.atomic():
                created = 0
                for row in data:
                    obj, created_flag = self.model.objects.get_or_create(**row)
                    if created_flag:
                        created += 1
        except Exception as exc:
            self.stderr.write(self.style.ERROR(
                f'Ошибка при сохранении данных: {exc}'
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Импорт из {self.data_path.name} завершён:'
            f'добавлено {created} {self.verbose_model_name}'
        ))
