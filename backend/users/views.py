from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import DefaultPagination
from api.serializers import (AvatarSerializer, SubscriberListSerializer,
                             SubscribeSerializer)

from .models import Subscriber

User = get_user_model()


class UserMeViewSet(UserViewSet):
    permission_classes = [IsAuthenticated]

    def me(self, request):
        return Response(self.get_serializer(request.user).data)


class AvatarPutDeleteView(APIView):
    permission_classes = (IsAuthenticated, )

    def put(self, request):
        user = request.user
        serializer = AvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response('Аватар отсутствует',
                        status=status.HTTP_400_BAD_REQUEST)


class SubcribeView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, pk):
        subscribe_to = get_object_or_404(User, id=pk)
        serializer = SubscribeSerializer(
            data={'subscribe_to': subscribe_to},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(subscriber=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        user = request.user
        unsub_author = get_object_or_404(User, id=pk)

        deleted_count, _ = Subscriber.objects.filter(
            subscriber=user, subscribe_to=unsub_author
        ).delete()

        if deleted_count == 0:
            return Response(
                {'Ошибка': 'Вы не были подписаны на автора!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'Сообщение': 'Вы успешно отписались от автора!'},
            status=status.HTTP_204_NO_CONTENT
        )


class SubscribeListView(APIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = DefaultPagination

    def get(self, request):
        paginator = self.pagination_class()
        user = request.user
        subscriptions = user.subscriber.all()
        subscribed_users = subscriptions.values('subscribe_to')
        paginated_subscriptions = paginator.paginate_queryset(subscribed_users,
                                                              request)
        serializer = SubscriberListSerializer(paginated_subscriptions,
                                              many=True,
                                              context={'request': request})
        return paginator.get_paginated_response(serializer.data)
