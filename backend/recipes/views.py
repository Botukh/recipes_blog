from django.shortcuts import redirect, get_object_or_404

from recipes.models import Recipe


def short_link_redirect(request, recipe_id):
    """Редирект с короткой ссылки на страницу рецепта."""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe.id}/')
