from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Recipe
from .fields import Base64ImageField


class UserMiniSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'first_name', 'last_name', 'avatar')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)
    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time', 'author')
