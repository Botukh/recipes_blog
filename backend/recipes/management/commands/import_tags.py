import pathlib

from recipes.models import Tag
from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт тегов из data/tags.json'
    model = Tag
    data_path = pathlib.Path('data/tags.json')
    verbose_model_name = 'тегов'
