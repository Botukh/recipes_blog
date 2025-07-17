from django.shortcuts import redirect, get_object_or_404
from django.http import Http404

from recipes.models import Recipe
from api.utils import decode_base62


def short_link_redirect(request, code):
    """Редирект с короткой ссылки на страницу рецепта."""
    try:
        recipe_id = decode_base62(code)
    except ValueError:
        raise Http404("Неверный формат короткой ссылки")

    recipe = get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe.id}/')
