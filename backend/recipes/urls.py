from django.urls import path

from .views import short_link_redirect

urlpatterns = [
    path('s/<str:code>/', short_link_redirect, name='short_link'),
]
