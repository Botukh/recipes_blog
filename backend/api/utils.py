import string
from datetime import date
from io import BytesIO

from django.template.loader import render_to_string
from django.http import FileResponse
from django.db.models import Sum

from recipes.models import Recipe, RecipeIngredient


def generate_shopping_list(user):
    """Функция для создания списка покупок."""
    recipes_qs = Recipe.objects.filter(in_shoppingcarts__user=user)

    ingredients = (
        RecipeIngredient.objects
        .filter(recipe__in=recipes_qs)
        .values('ingredient__name', 'ingredient__unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )

    recipes = recipes_qs.values_list('name', 'author__username')

    context = {
        'date': date.today(),
        'ingredients': ingredients,
        'recipes': recipes,
    }

    content = render_to_string('shopping_list.txt', context)
    buffer = BytesIO()
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename='shopping_list.txt',
        content_type='text/plain'
    )


ALPHABET = string.digits + string.ascii_letters


def encode_base62(num: int) -> str:
    """Кодирует целое число в строку в системе base62."""
    if num == 0:
        return ALPHABET[0]
    arr = []
    base = len(ALPHABET)
    while num > 0:
        num, rem = divmod(num, base)
        arr.append(ALPHABET[rem])
    arr.reverse()
    return ''.join(arr)


def decode_base62(code: str) -> int:
    """Декодирует строку в base62 обратно в целое число."""
    base = len(ALPHABET)
    num = 0
    for char in code:
        if char not in ALPHABET:
            raise ValueError(f'Invalid character {char} in base62 code')
        num = num * base + ALPHABET.index(char)
    return num
