from rest_framework.routers import DefaultRouter
from django.urls import path, include
from recipes.views import RecipeViewSet, IngredientViewSet, TagViewSet
from users.views import UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('v1/', include(router.urls)),
]
