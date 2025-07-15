from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from recipes.models import Recipe


def short_link_redirect(request, recipe_id):
    """Редирект с короткой ссылки на страницу рецепта."""
    if not Recipe.objects.filter(id=recipe_id).exists():
        return HttpResponseRedirect('/')
    return redirect(f'/recipes/{recipe_id}/')
