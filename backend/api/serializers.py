from django.db import transaction
from rest_framework import serializers
from djoser.serializers import UserSerializer as DjoserBaseUserSerializer

from .fields import Base64ImageField
from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    Subscription,
    User
)
from recipes.constants import MIN_MEASURE


class UserSerializer(DjoserBaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserBaseUserSerializer.Meta):
        model = User
        fields = DjoserBaseUserSerializer.Meta.fields + ('is_subscribed',)
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user, author=obj).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class IngredientMeasureSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=MIN_MEASURE, source='measure')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class IngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientReadSerializer(
        many=True, source='recipe_ingredients', read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time', 'short_link'
        )
        read_only_fields = fields

    def get_short_link(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(f'/r/{obj.uuid}/')

    def _is_related(self, recipe: Recipe, model):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and model.objects.filter(user=user, recipe=recipe).exists()
        )

    def get_is_favorited(self, obj: Recipe):
        return self._is_related(obj, Favorite)

    def get_is_in_shopping_cart(self, obj: Recipe):
        return self._is_related(obj, ShoppingCart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientMeasureSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time',
        )

    def validate_ingredients(self, ingredients_data):
        if not ingredients_data:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент.'
            )
        self._validate_uniqueness(
            ingredients_data,
            key='ingredient',
            error_message='Ингредиенты должны быть уникальными. Повторы: {}'
        )
        return ingredients_data

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Нужно указать хотя бы один тег.'
            )
        self._validate_uniqueness(
            tags,
            error_message='Теги должны быть уникальными. Повторы: {}'
        )
        return tags

    @staticmethod
    def _validate_uniqueness(items, key=None, error_message='Повторы: {}'):
        seen = set()
        duplicates = set()

        for item in items:
            value = item[key] if key else item
            if value in seen:
                duplicates.add(value)
            seen.add(value)

        if duplicates:
            raise serializers.ValidationError(
                error_message.format(', '.join(str(d) for d in duplicates))
            )

    @staticmethod
    def _bulk_create_ingredients(recipe: Recipe, ingredients_data: list[dict]):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                measure=item['measure']
            )
            for item in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create({
            **validated_data,
            'author': self.context['request'].user
        })
        recipe.tags.set(tags)
        self._bulk_create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, recipe: Recipe, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().update(recipe, validated_data)
        recipe.tags.set(tags)
        recipe.recipe_ingredients.all().delete()
        self._bulk_create_ingredients(recipe, ingredients_data)
        return recipe

    def to_representation(self, recipe: Recipe):
        return RecipeReadSerializer(recipe, context=self.context).data
