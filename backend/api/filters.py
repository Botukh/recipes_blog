from django.db.models import Exists, OuterRef
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag, ShoppingCart


class IngredientSearchFilter(SearchFilter):
    search_param = "name"


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all()
    )
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_is_in_cart")

    class Meta:
        model = Recipe
        fields = (
            "tags",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def _boolean_param(self, value):
        return value in (True, "1", 1, "true", "True", "") or value is None

    def filter_is_favorited(self, qs, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return qs
        return (
            qs.filter(in_favorites__user=user)
            if self._boolean_param(value)
            else qs
        )

    def filter_is_in_cart(self, qs, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return qs
        if not self._boolean_param(value):
            return qs
        sub_qs = ShoppingCart.objects.filter(user=user, recipe=OuterRef("pk"))
        return qs.annotate(
            in_cart=Exists(sub_qs)).filter(in_cart=True
                                           ).order_by("id").distinct("id")
