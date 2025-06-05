from rest_framework.routers import DefaultRouter
from django.urls import path, include
from recipes.views import RecipeViewSet, IngredientViewSet, TagViewSet
from users.views import UserViewSet

router_v1 = DefaultRouter()
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
]
