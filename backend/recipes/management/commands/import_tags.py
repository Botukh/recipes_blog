from pathlib import Path

from recipes.models import Tag
from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    model = Tag
    data_path = Path('data/tags.json')
