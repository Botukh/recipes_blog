from datetime import date
from django.template.loader import render_to_string
from django.db.models import Sum

from recipes.models import RecipeIngredient


def generate_shopping_list(user):
    """Функция для создания списка покупок."""
    recipes_qs = RecipeIngredient.objects.filter(
        recipe__in_shoppingcarts__user=user
    ).select_related('ingredient', 'recipe')

    ingredients = (
        recipes_qs
        .values('ingredient__name', 'ingredient__unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )

    recipes = (
        recipes_qs
        .values_list('recipe__name', 'recipe__author__username')
        .distinct()
    )

    context = {
        'date': date.today(),
        'ingredients': ingredients,
        'recipes': recipes,
    }

    return render_to_string('shopping_list.txt', context)
