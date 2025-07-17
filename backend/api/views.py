from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
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
    Ingredient,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)
from .serializers import (
    SubscriptionSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)
from .filters import RecipeFilter, IngredientSearchFilter
from .utils import generate_shopping_list, encode_base62


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related(
        'tags',
        'in_favorites',
        'in_shoppingcarts',
        'ingredient_amounts__ingredient',
    )

    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_to(self, model, user, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = model.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            raise ValidationError(
                f'Рецепт "{recipe}" уже добавлен в список'
                f'{model._meta.verbose_name_plural.lower()}.'
            )
        return Response(
            RecipeReadSerializer(
                recipe, context={'request': self.request}).data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def _remove_from(model, user, pk):
        get_object_or_404(model, user=user, recipe_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        code = encode_base62(recipe.id)
        short_url = request.build_absolute_uri(
            reverse('short_link', args=[code])
        )
        return Response({'short-link': short_url})

    @action(detail=True, methods=['post'], url_path='favorite',
            permission_classes=[IsAuthenticated])
    def add_to_favorite(self, request, pk=None):
        return self._add_to(Favorite, request.user, pk)

    @add_to_favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        return self._remove_from(Favorite, request.user, pk)

    @action(detail=True, methods=['post'], url_path='shopping_cart',
            permission_classes=[IsAuthenticated])
    def add_to_shopping_cart(self, request, pk=None):
        return self._add_to(ShoppingCart, request.user, pk)

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self._remove_from(ShoppingCart, request.user, pk)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart',
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        return generate_shopping_list(request.user)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class UserViewSet(DjoserUserView):

    @action(
        detail=False,
        methods=['put'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='me-avatar'
    )
    def upload_avatar(self, request):
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        authors = User.objects.filter(authors__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if author == request.user:
                raise serializers.ValidationError(
                    'Нельзя подписаться на себя.'
                )

            if Subscription.objects.filter(
                user=request.user, author=author
            ).exists():
                raise serializers.ValidationError(
                    'Вы уже подписаны на этого пользователя.'
                )

            Subscription.objects.create(user=request.user, author=author)
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        get_object_or_404(
            Subscription, user=request.user, author=author
        ).delete()
        return Response(
            {'detail': 'Подписка удалена'}, status=status.HTTP_204_NO_CONTENT
        )
