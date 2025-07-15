import pathlib

from recipes.models import Ingredient

from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт ингредиентов из data/ingredients.json'
    model = Ingredient
    data_path = pathlib.Path('data/ingredients.json')
    verbose_model_name = 'ингредиентов'
