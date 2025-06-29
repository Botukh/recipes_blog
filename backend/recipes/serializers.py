from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .fields import Base64ImageField
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


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


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class IngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserMiniSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_ingredients(self, obj: Recipe) -> list[dict]:
        ingredients = obj.recipe_ingredients.select_related('ingredient')
        return IngredientReadSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj: Recipe) -> bool:
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and Favorite.objects.filter(user=user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент.',
            )
        seen: set[Ingredient] = set()
        for item in value:
            ing = item['ingredient']
            if ing in seen:
                raise serializers.ValidationError(
                    'Ингредиенты должны быть уникальными.',
                )
            seen.add(ing)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно указать хотя бы один тег.',
            )
        if len(set(value)) != len(value):
            raise serializers.ValidationError('Теги должны быть уникальными.')
        return value

    @staticmethod
    def _bulk_create_ingredients(recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(
            **validated_data,
            author=self.context['request'].user,
        )
        recipe.tags.set(tags)
        self._bulk_create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self._bulk_create_ingredients(instance, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class _BaseUserRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        abstract = True
        fields = ('user', 'recipe')
        read_only_fields = ('user', 'recipe')

    ERR_EXISTS = 'Запись уже существует.'

    def create(self, validated_data):
        request = self.context['request']
        recipe = self.context['recipe']
        try:
            obj, _ = self.Meta.model.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            return obj
        except IntegrityError:
            raise serializers.ValidationError(self.ERR_EXISTS)


class FavoriteSerializer(_BaseUserRecipeSerializer):
    ERR_EXISTS = 'Рецепт уже добавлен в избранное.'

    class Meta(_BaseUserRecipeSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(_BaseUserRecipeSerializer):
    ERR_EXISTS = 'Рецепт уже находится в списке покупок.'

    class Meta(_BaseUserRecipeSerializer.Meta):
        model = ShoppingCart
