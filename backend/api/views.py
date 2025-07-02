from datetime import date
from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from djoser.views import UserViewSet as DjoserUserView

from recipes.models import (
    Favorite,
    Product,
    Recipe,
    RecipeProduct,
    ShoppingCart,
    Tag,
    Subscription,
    User,
)
from api.serializers import (
    RecipeSerializer,
    RecipeShortSerializer,
    ProductSerializer,
    TagSerializer,
)
from api.filters import RecipeFilter, ProductSearchFilter

__all__ = [
    'RecipeViewSet',
    'ProductViewSet',
    'TagViewSet',
    'UserViewSet',
]


def _add_relation(model, user, recipe_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk)
    _, created = model.objects.get_or_create(user=user, recipe=recipe)
    if not created:
        return Response({'errors': 'Уже добавлено'}, status=400)
    return Response(
        RecipeShortSerializer(recipe, context={'request': None}).data,
        status=201
    )


def _remove_relation(model, user, recipe_pk):
    obj = get_object_or_404(model, user=user, recipe__pk=recipe_pk)
    obj.delete()
    return Response(status=204)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_class = RecipeFilter
    serializer_class = RecipeSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return _add_relation(Favorite, request.user, pk)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return _remove_relation(Favorite, request.user, pk)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return _add_relation(ShoppingCart, request.user, pk)

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        return _remove_relation(ShoppingCart, request.user, pk)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        products = (
            RecipeProduct.objects
            .filter(recipe__shoppingcart__user=request.user)
            .values('product__name', 'product__unit')
            .annotate(total=Sum('measure'))
            .order_by('product__name')
        )
        recipes_info = (
            Recipe.objects
            .filter(shoppingcart__user=request.user)
            .values_list('name', 'author__username')
        )

        date_str = date.today().strftime('%d.%m.%Y')
        product_lines = [
            f"{i}. {p['product__name'].capitalize()} — "
            f"{p['total']} {p['product__unit']}"
            for i, p in enumerate(products, 1)
        ]
        recipe_lines = [
            f'- {name} (автор: {author})'
            for name, author in recipes_info
        ]

        lines = [
            f'Список покупок от {date_str}',
            '',
            'Продукты:',
            *product_lines,
            '',
            'Рецепты:',
            *recipe_lines,
        ]

        buffer = BytesIO('\n'.join(lines).encode())
        return FileResponse(
            buffer, as_attachment=True, filename='shopping_list.txt'
        )


class ProductViewSet(ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)
    filter_backends = (ProductSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class UserViewSet(DjoserUserView):

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        authors = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(authors)
        data = RecipeShortSerializer(
            page, many=True, context={'request': request}
        ).data
        return self.get_paginated_response(data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            if author == request.user:
                return Response(
                    {'errors': 'Нельзя подписаться на себя'},
                    status=400
                )
            Subscription.objects.get_or_create(
                user=request.user, author=author
            )
            return Response(status=201)
        sub = get_object_or_404(
            Subscription, user=request.user, author=author
        )
        sub.delete()
        return Response(status=204)
