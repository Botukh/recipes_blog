from pathlib import Path

from recipes.models import Ingredient

from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    model = Ingredient
    data_path = Path('data/ingredients.json')
