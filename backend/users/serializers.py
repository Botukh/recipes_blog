from rest_framework import serializers
from recipes.fields import Base64ImageField
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.templatetags.static import static

from .models import User, Subscription
from recipes.serializers_minified import RecipeMinifiedSerializer


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            "avatar_url",
            'is_subscribed'
        )
        read_only_fields = ("avatar_url", "is_subscribed")

    def get_avatar_url(self, obj):
        request = self.context["request"]
        try:
            url = obj.avatar.url
        except ValueError:
            url = static("users/avatar-icon.png")
        return request.build_absolute_uri(url)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        )


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = list(CustomUserSerializer.Meta.fields) + ['recipes', 'recipes_count']

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipe_set.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipe_set.count()
