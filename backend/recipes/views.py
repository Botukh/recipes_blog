from django.shortcuts import render
from django.http import Http404

from recipes.models import Recipe
from api.utils import decode_base62


def short_link_redirect(request, code):
    """Возвращает страницу фронтенда для короткой ссылки."""
    try:
        recipe_id = decode_base62(code)
    except ValueError:
        raise Http404("Неверный формат короткой ссылки")

    if not Recipe.objects.filter(id=recipe_id).exists():
        raise Http404("Рецепт не найден")

    return render(request, 'index.html')
