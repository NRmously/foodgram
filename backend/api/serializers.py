from djoser.serializers import UserCreateSerializer
from rest_framework import serializers, status
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator

from api.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscriber, User


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


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('id', 'name', 'measurement_unit')


class CreateIngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
        error_messages={
            'does_not_exist': 'Указанный ингредиент не существует'
        }
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)


class IngredientSerializer(serializers.ModelSerializer):
    amount = RecipeIngredientSerializer(read_only=True)

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserListSerializer(required=False)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients',
        many=True,
        read_only=True,
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return obj.favorite.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return obj.shopcart.filter(user=request.user).exists()
        return False


class RecipeSerializer(serializers.ModelSerializer):
    author = UserListSerializer(required=False)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=True)
    image = Base64ImageField(required=True, allow_null=True)
    ingredients = CreateIngredientInRecipeSerializer(
        many=True, source='recipe_ingredients', required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text',
                  'cooking_time')

    def create_recipe_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient.get('ingredient'),
            amount=ingredient.get('amount'),)
            for ingredient in ingredients)

    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_recipe_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = validated_data.pop('recipe_ingredients', [])
        tags = validated_data.pop('tags', [])
        instance.tags.set(tags)
        self.create_recipe_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data

    def validate(self, value):
        tags = value.get('tags')
        ingredients = value.get('recipe_ingredients')
        if not tags:
            raise serializers.ValidationError(
                'Теги не могут быть пустыми', status.HTTP_400_BAD_REQUEST)
        if not ingredients:
            raise serializers.ValidationError(
                'Ингредиенты не могут быть пустыми',
                status.HTTP_400_BAD_REQUEST)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Теги не могут быть пустыми', status.HTTP_400_BAD_REQUEST)
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Теги должны быть уникальными', status.HTTP_400_BAD_REQUEST)
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Ингредиенты не могут быть пустыми',
                status.HTTP_400_BAD_REQUEST
            )
        ingredients_set = set()
        for item in value:
            ingredient = item['ingredient']
            if ingredient in ingredients_set:
                raise serializers.ValidationError(
                    f'Ингредиент "{ingredient}" уже добавлен в рецепт.',
                    status.HTTP_400_BAD_REQUEST
                )
            ingredients_set.add(ingredient)
        return value


class DetailSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class BaseFavoriteAndShopCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('author', 'recipe')

    def to_representation(self, instance):
        return DetailSerializer(instance).data


class FavoriteSerializer(BaseFavoriteAndShopCartSerializer):
    class Meta(BaseFavoriteAndShopCartSerializer.Meta):
        model = Favorite


class ShopCartSerializer(BaseFavoriteAndShopCartSerializer):
    class Meta:
        model = ShoppingCart


class RecipForSubscribersSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


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
        limit = int(request.GET.get('recipes_limit', 10))
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

    def validate_subscribe_to(self, value):
        subscriber = self.context['request'].user
        if subscriber == value:
            raise serializers.ValidationError("Нельзя подписаться на себя!")
        return value


class SubscriberListSerializer(SubscribeRecipesBase):
    class Meta(UserListSerializer.Meta):
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )
