from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from recipes.models import Recipe

User = get_user_model()


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class RecipeFilter(filters.FilterSet):

    tags = CharInFilter(
        field_name='tags__slug',
        lookup_expr='in',
        help_text='Фильтр по slug тегов, через запятую',
    )
    author = filters.ModelChoiceFilter(
        field_name='author',
        queryset=User.objects.all(),
        help_text='Фильтр по id автора',
    )
    is_favorited = filters.BooleanFilter(
        method='filter_favorited',
        help_text=(
            'Только рецепты, добавленные в избранное '
            'текущим пользователем'
        ),
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_cart',
        help_text=(
            'Только рецепты, добавленные в список покупок '
            'текущим пользователем'
        ),
    )

    class Meta:
        model = Recipe
        fields = [
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        ]

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            if not user.is_authenticated:
                return queryset.none()
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            if not user.is_authenticated:
                return queryset.none()
            return queryset.filter(in_carts__user=user)
        return queryset
