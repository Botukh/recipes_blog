from datetime import date

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

    return FileResponse(
        content,
        as_attachment=True,
        filename='shopping_list.txt',
        content_type='text/plain'
    )
