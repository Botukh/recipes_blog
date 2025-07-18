from django.shortcuts import redirect
from django.core.exceptions import ValidationError

from recipes.models import Recipe


def short_link_redirect(request, recipe_id):
    """Редирект с короткой ссылки на страницу рецепта."""
    if not Recipe.objects.filter(id=recipe_id).exists():
        raise ValidationError(f'Рецепт с id={recipe_id} не найден.')
    return redirect(f'/recipes/{recipe_id}/')
