from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, AllowAny
)
from rest_framework.response import Response

from .models import (
    Recipe, Favorite, ShoppingCart, RecipeIngredient,
    Ingredient, Tag
)
from .serializers import (
    RecipeReadSerializer, RecipeWriteSerializer,
    IngredientSerializer, TagSerializer
)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_to(self, model, user, recipe):
        if not user.is_authenticated:
            raise ValidationError('Необходима авторизация.')
        if model.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Рецепт уже добавлен.')
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeReadSerializer(
            recipe,
            context={'request': self.request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from(self, model, user, recipe):
        if not user.is_authenticated:
            raise ValidationError('Необходима авторизация.')
        obj = model.objects.filter(user=user, recipe=recipe)
        if not obj.exists():
            raise ValidationError('Рецепта нет в списке.')
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return self._add_to(Favorite, request.user, recipe)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return self._remove_from(Favorite, request.user, recipe)

    @action(detail=True, methods=['post'])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return self._add_to(ShoppingCart, request.user, recipe)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return self._remove_from(ShoppingCart, request.user, recipe)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Требуется авторизация'}, status=401)

        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

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


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['^name']


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
