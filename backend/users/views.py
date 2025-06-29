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

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        author = self.get_object()

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={},
                context={'request': request, 'author': author}
            )
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return Response(
                SubscriptionSerializer(
                    instance, context={'request': request}
                    ).data,
                status=status.HTTP_201_CREATED
            )

        deleted, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Не была подписана'},
                        status=status.HTTP_400_BAD_REQUEST)

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
