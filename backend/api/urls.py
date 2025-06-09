# api/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from recipes.views import RecipeViewSet, IngredientViewSet, TagViewSet
from users.views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls.authtoken')),
]
