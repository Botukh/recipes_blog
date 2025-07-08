from rest_framework import serializers
from djoser.serializers import UserSerializer as DjoserBaseUserSerializer

from recipes.models import (
    Recipe,
    Tag,
    Product,
    RecipeProduct,
    Favorite,
    ShoppingCart,
    Subscription,
    User
)
from recipes.constants import MIN_MEASURE


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class ProductMeasureSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product")
    measure = serializers.IntegerField(min_value=MIN_MEASURE)

    class Meta:
        model = RecipeProduct
        fields = ("id", "measure")


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    products = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = "__all__"
        read_only_fields = fields

    def get_products(self, recipe):
        return [
            {
                "id": rp.product.id,
                "name": rp.product.name,
                "unit": rp.product.unit,
                "measure": rp.measure,
            }
            for rp in recipe.recipe_products.select_related("product")
        ]

    def _has_relation(self, recipe, model):
        user = self.context["request"].user
        return user.is_authenticated and model.objects.filter(
            user=user, recipe=recipe).exists()

    def get_is_favorited(self, recipe):
        return self._has_relation(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self._has_relation(recipe, ShoppingCart)


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
