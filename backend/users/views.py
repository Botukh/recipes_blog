# users/views.py
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from .models import Subscription, User
from .serializers import SubscriptionSerializer


class UserViewSet(DjoserUserViewSet):

    @action(detail=False,
            permission_classes=[IsAuthenticated],
            serializer_class=SubscriptionSerializer)
    def subscriptions(self, request, *args, **kwargs):
        authors = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=["post", "delete"],
            permission_classes=[IsAuthenticated],
            serializer_class=SubscriptionSerializer)
    def subscribe(self, request, *args, **kwargs):
        author = self.get_object()

        if request.method == "POST":
            if author == request.user:
                return Response(
                    {"errors": "Нельзя подписаться на себя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            obj, created = Subscription.objects.get_or_create(
                user=request.user, author=author
            )
            if not created:
                return Response(
                    {"errors": "Вы уже подписаны"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                self.get_serializer(author).data,
                status=status.HTTP_201_CREATED,
            )

        deleted, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"errors": "Подписки не существует"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False,
        methods=["put", "patch"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
        url_name="me-avatar",
    )
    def set_avatar(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
