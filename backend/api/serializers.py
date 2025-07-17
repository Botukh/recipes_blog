from collections import Counter

from django.db import transaction
from djoser.serializers import UserSerializer as DjoserBaseUserSerializer
from rest_framework import serializers

from recipes.constants import MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Subscription,
    Tag,
    User,
)
from .fields import Base64ImageField


class UserSerializer(DjoserBaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta(DjoserBaseUserSerializer.Meta):
        model = User
        fields = (
            *DjoserBaseUserSerializer.Meta.fields, 'is_subscribed', 'avatar')
        read_only_fields = fields

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
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientMeasureSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and Subscription.objects.filter(user=user, author=obj).exists()
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        limit = request.query_params.get('recipes_limit')

        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class IngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')
        read_only_fields = fields


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientReadSerializer(
        many=True,
        source='ingredient_amounts',
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = fields

    def _is_related(self, recipe: Recipe, related_name: str):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return getattr(recipe, related_name).filter(user=user).exists()

    def get_is_favorited(self, recipe: Recipe):
        return self._is_related(recipe, 'in_favorites')

    def get_is_in_shopping_cart(self, recipe: Recipe):
        return self._is_related(recipe, 'in_shoppingcarts')


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientMeasureSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate(self, data):
        ingredients_data = data.get('ingredients')
        tags_data = data.get('tags')

        self._validate_uniqueness(
            values=[item['ingredient'] for item in ingredients_data],
            error_message='Ингредиенты должны быть уникальными. Повторы: {}',
            field='ingredients',
            empty_message='Необходимо указать хотя бы один ингредиент.'
        )

        self._validate_uniqueness(
            values=tags_data,
            error_message='Теги должны быть уникальными. Повторы: {}',
            field='tags',
            empty_message='Нужно указать хотя бы один тег.'
        )

        return data

    @staticmethod
    def _validate_uniqueness(values, error_message, field, empty_message):
        if not values:
            raise serializers.ValidationError({field: empty_message})
        duplicates = [item for item, count in Counter(
            values
        ).items() if count > 1]
        if duplicates:
            raise serializers.ValidationError(
                {field: error_message.format(duplicates)}
            )

    @staticmethod
    def _bulk_create_ingredients(recipe: Recipe, ingredients_data: list[dict]):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self._bulk_create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance: Recipe, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredient_amounts.all().delete()
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        self._bulk_create_ingredients(instance, ingredients_data)
        return instance

    def to_representation(self, recipe: Recipe):
        return RecipeReadSerializer(recipe, context=self.context).data
