from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.api.filters import RecipeFilter
from apps.api.pagination import LimitPageNumberPagination
from apps.api.permissions import IsAuthorOrReadOnly
from .models import Recipe, Tag, Ingredient, Favorite, ShoppingCart, RecipeIngredient
from .serializers import (
    TagSerializer, IngredientSerializer,
    RecipeListSerializer, RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = {'name': ['istartswith']}


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    pagination_class = LimitPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    @action(
        detail=True, methods=['get'],
        permission_classes=(AllowAny,)
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        # Предполагаем, что у Recipe есть метод get_short_link()
        return Response(
            {'short-link': recipe.get_short_link()}
        )

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=user, recipe=recipe)
            data = RecipeMinifiedSerializer(recipe).data
            return Response(data, status=status.HTTP_201_CREATED)
        deleted, _ = Favorite.objects.filter(user=user, recipe=recipe).delete()
        if not deleted:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=user, recipe=recipe)
            data = RecipeMinifiedSerializer(recipe).data
            return Response(data, status=status.HTTP_201_CREATED)
        deleted, _ = ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
        if not deleted:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        qs = RecipeIngredient.objects.filter(
            recipe__in_carts__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total=Sum('amount'))
        lines = [
            f"{i['ingredient__name']} ({i['ingredient__measurement_unit']}) — {i['total']}"
            for i in qs
        ]
        content = '\n'.join(lines)
        return HttpResponse(
            content, content_type='text/plain',
            headers={'Content-Disposition': 'attachment; filename="shopping.txt"'}
        )
