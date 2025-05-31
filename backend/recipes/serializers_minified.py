from rest_framework import serializers
from .models import Recipe
from .fields import Base64ImageField


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
