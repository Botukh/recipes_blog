from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import User, Follow
from .serializers import (
    CustomUserCreateSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
    SetAvatarSerializer,
    SetAvatarResponseSerializer,
    SetPasswordSerializer
)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    create_serializer_class = CustomUserCreateSerializer
    serializer_class = UserSerializer

    @action(
        detail=False, methods=['get'],
        permission_classes=(IsAuthenticated,),
        serializer_class=UserSerializer
    )
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

    @action(
        detail=False, methods=['put', 'delete'],
        permission_classes=(IsAuthenticated,),
        serializer_class=SetAvatarSerializer
    )
    def avatar(self, request):
        if request.method == 'DELETE':
            request.user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.avatar = serializer.validated_data['avatar']
        request.user.save()
        out = SetAvatarResponseSerializer(request.user)
        return Response(out.data)

    @action(
        detail=False, methods=['post'],
        permission_classes=(IsAuthenticated,),
        serializer_class=SetPasswordSerializer
    )
    def set_password(self, request):
        serializer = self.get_serializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user
        if request.method == 'POST':
            if author == user or Follow.objects.filter(
                user=user,
                author=author
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            Follow.objects.create(user=user, author=author)
            data = UserWithRecipesSerializer(
                author, context={'request': request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)
        deleted, _ = Follow.objects.filter(user=user, author=author).delete()
        if not deleted:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'],
        permission_classes=(IsAuthenticated,),
        serializer_class=UserWithRecipesSerializer
    )
    def subscriptions(self, request):
        subs = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(subs)
        data = self.get_serializer(page, many=True).data
        return self.get_paginated_response(data)
