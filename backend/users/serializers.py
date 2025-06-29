from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from recipes.fields import Base64ImageField
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.templatetags.static import static

from .models import User, Subscription


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
        extra_kwargs = {"avatar": {"required": False}}

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


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author', 'created_at')
        read_only_fields = ('user', 'author', 'created_at')

    def create(self, validated_data):
        request = self.context['request']
        author = self.context['author']

        if request.user == author:
            raise ValidationError('Нельзя подписаться на себя.')

        try:
            sub, _ = Subscription.objects.get_or_create(
                user=request.user, author=author
            )
            return sub
        except IntegrityError:
            raise ValidationError('Вы уже подписаны на этого автора.')
