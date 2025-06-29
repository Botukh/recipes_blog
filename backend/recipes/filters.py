from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_carts = filters.BooleanFilter(
        method='filter_is_in_shopping_carts',
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_carts')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        true_values = (True, '1', 1, 'true', 'True')
        if value in true_values and user.is_authenticated:
            return queryset.filter(favorited_by__user=user).distinct()
        if (value == '' or value is None) and user.is_authenticated:
            return queryset.none()
        return queryset

    def filter_is_in_shopping_carts(self, queryset, name, value):
        user = self.request.user
        true_values = (True, '1', 1, 'true', 'True')
        if value in true_values and user.is_authenticated:
            return queryset.filter(in_shopping_carts__user=user).distinct()
        if (value == '' or value is None) and user.is_authenticated:
            return queryset.none()
        return queryset
