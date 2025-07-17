from django.http import Http404, HttpResponseRedirect

from .models import Recipe
from api.utils import decode_base62


def short_link_redirect(request, code):
    """Редирект на страницу рецепта по короткой ссылке."""
    try:
        recipe_id = decode_base62(code)
    except ValueError:
        raise Http404("Неверный формат короткой ссылки")

    if not Recipe.objects.filter(id=recipe_id).exists():
        raise Http404("Рецепт не найден")

    return HttpResponseRedirect(f'/recipes/{recipe_id}/')
