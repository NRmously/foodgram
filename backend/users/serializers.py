from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator

from api.fields import Base64ImageField

from .models import Subscriber, User


class UserListSerializer(ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return author.subscriber_to.filter(subscriber=request.user,
                                               subscribe_to=author).exists()
        return False


class UserCreatesSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class UserMeSerializer(UserListSerializer):
    pass


class AvatarSerializer(ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SubscribeRecipesBase(UserListSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta(UserListSerializer.Meta):
        fields = UserListSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def get_recipes(self, author):
        from api.serializers import RecipForSubscribersSerializer
        recipes = author.recipes.all()
        request = self.context['request']
        limit = request.GET.get('recipes_limit')
        if limit:
            recipes = recipes[: int(limit)]
        serializer = RecipForSubscribersSerializer(recipes,
                                                   many=True,
                                                   read_only=True)
        return serializer.data


class UserRecipeSerializer(SubscribeRecipesBase):
    pass


class SubscribeSerializer(serializers.ModelSerializer):
    subscriber = serializers.SlugRelatedField(
        read_only=True,
        slug_field='email',
        default=serializers.CurrentUserDefault(),
    )
    subscribe_to = serializers.SlugRelatedField(
        slug_field='email',
        queryset=User.objects.all(),
    )

    class Meta:
        model = Subscriber
        fields = ('subscribe_to', 'subscriber')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('subscribe_to', 'subscriber'),
                message='Вы уже подписаны на этого пользователя!',
            )
        ]

    def to_representation(self, instance):
        return UserRecipeSerializer(instance.subscribe_to,
                                    context=self.context).data


class SubscriberListSerializer(SubscribeRecipesBase):
    class Meta(UserListSerializer.Meta):
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )
