from __future__ import annotations

from django.db.models import Sum
from django.http import HttpResponse

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response


from .filters import IngredientSearchFilter, RecipeFilter
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from .serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        return (
            RecipeReadSerializer
            if self.action in ('list', 'retrieve') else
            RecipeWriteSerializer
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def _remove_from(model, user, recipe):
        """Общее удаление из Favorite / ShoppingCart."""
        if not user.is_authenticated:
            raise ValidationError('Необходима авторизация.')
        deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if not deleted:
            raise ValidationError('Рецепта нет в списке.')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        url_path='favorite',
        permission_classes=[IsAuthenticatedOrReadOnly],
    )
    def add_to_favorite(self, request, pk=None):
        recipe = self.get_object()
        serializer = FavoriteSerializer(
            data={}, context={'request': request, 'recipe': recipe},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        data = RecipeReadSerializer(recipe,
                                    context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @add_to_favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        recipe = self.get_object()
        return self._remove_from(Favorite, request.user, recipe)

    @action(
        detail=True,
        methods=['post'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticatedOrReadOnly],
    )
    def add_to_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        serializer = ShoppingCartSerializer(
            data={}, context={'request': request, 'recipe': recipe},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        data = RecipeReadSerializer(recipe,
                                    context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self._remove_from(ShoppingCart, request.user, recipe)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticatedOrReadOnly],
    )
    def download_shopping_cart(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Требуется авторизация'},
                            status=status.HTTP_401_UNAUTHORIZED)

        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in_shopping_cart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        lines = [
            f"{item['ingredient__name']} "
            f"({item['ingredient__measurement_unit']}) — "
            f"{item['total_amount']}"
            for item in ingredients
        ]
        content = '\n'.join(lines)

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [IngredientSearchFilter]
    search_fields = ['^name']
    pagination_class = None


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None
