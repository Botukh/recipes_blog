from django.shortcuts import get_object_or_404, redirect
from django.views import View

from rest_framework import status, viewsets
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
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
    Subscription,
    User,
)
from .serializers import (
    RecipeShortSerializer,
    IngredientSerializer,
    TagSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer
)
from .filters import RecipeFilter, IngredientSearchFilter
from .utils import generate_shopping_list

__all__ = [
    'RecipeViewSet',
    'IngredientViewSet',
    'TagViewSet',
    'UserViewSet',
]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def _remove_from(model, user, pk):
        obj = get_object_or_404(model, user=user, recipe_id=pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _add_to(self, model, user, pk):
        if model.objects.filter(user=user, recipe_id=pk).exists():
            return Response(
                {'errors': 'Рецепт уже в списке.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe = get_object_or_404(Recipe, pk=pk)
        model.objects.create(user=user, recipe=recipe)
        data = RecipeReadSerializer(
            recipe, context={'request': self.request}).data
        return Response(data, status=status.HTTP_201_CREATED)

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


class RecipeRedirectView(View):
    def get(self, request, uuid):
        recipe = get_object_or_404(Recipe, uuid=uuid)
        return redirect('frontend-recipe-url', pk=recipe.id)


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

    @action(detail=False, methods=['post', 'put'],
            permission_classes=[IsAuthenticated],
            url_path="me/avatar",
            url_name="me-avatar",)
    def upload_avatar(self, request):
        user = request.user
        avatar = request.FILES.get('avatar')

        if not avatar:
            return Response({'error': 'Аватар не передан.'}, status=400)

        user.avatar = avatar
        user.save()
        return Response({'status': 'Аватар загружен'}, status=200)

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
