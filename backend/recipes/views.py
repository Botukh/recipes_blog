from django.shortcuts import redirect
from django.http import Http404

from recipes.models import Recipe


def short_link_redirect(request, recipe_id):
    """Редирект на страницу рецепта по короткой ссылке."""
    if not Recipe.objects.filter(id=recipe_id).exists():
        raise Http404(f'Рецепт с id={recipe_id} не найден.')
    return redirect(request.build_absolute_uri(f'/recipes/{recipe_id}'))
