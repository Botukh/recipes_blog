from django.urls import path

from .views import short_link_redirect


urlpatterns = [
    path(
        'short/<int:recipe_id>/', short_link_redirect, name='recipe-short-url'
    ),
]
