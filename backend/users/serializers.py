import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import (
    UserCreateSerializer,
    UserSerializer as BaseUserSerializer
)
from apps.recipes.serializers import RecipeMinifiedSerializer
from .models import User


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')


class UserSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.following.filter(user=user).exists()


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context['request']
        limit = request.query_params.get('recipes_limit')
        qs = obj.recipes.all()
        if limit:
            try:
                limit = int(limit)
                qs = qs[:limit]
            except ValueError:
                pass
        return RecipeMinifiedSerializer(qs, many=True).data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, base64_data = data.split(';base64,')
            decoded = base64.b64decode(base64_data)
            file_name = f'{uuid.uuid4()}.png'
            data = ContentFile(decoded, name=file_name)
        return super().to_internal_value(data)


class SetAvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField()


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль')
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
