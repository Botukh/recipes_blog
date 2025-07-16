from datetime import date
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum

from recipes.models import Recipe, RecipeIngredient

def generate_shopping_list(user):
    recipes_qs = Recipe.objects.filter(shoppingcart__user=user)

    ingredients = (
        RecipeIngredient.objects
        .filter(recipe__in=recipes_qs)
        .values('ingredient__name', 'ingredient__unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )

    recipes = recipes_qs.values_list('name', 'author__username')

    context = {
        'date': date.today().strftime('%d.%m.%Y'),
        'ingredients': ingredients,
        'recipes': recipes,
    }

    print('>>> ingredients:', list(ingredients))
    print('>>> recipes:', list(recipes))

    content = render_to_string('shopping_list.txt', context)
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.txt"')
    return response
