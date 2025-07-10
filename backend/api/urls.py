from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProductViewSet,
    RecipeViewSet,
    TagViewSet,
    UserViewSet,
    RecipeRedirectView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'r/<uuid:uuid>/', RecipeRedirectView.as_view(), name='recipe-short-url'
    ),
]
