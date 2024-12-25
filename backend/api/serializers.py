from rest_framework import serializers, status

from api.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipes, RecipesIngredient,
                            ShoppingCart, Tag)
from users.serializers import UserListSerializer


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipesIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class CreateIngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
        error_messages={
            'does_not_exist': 'Указанный ингредиент не существует'
        }
    )

    class Meta:
        model = RecipesIngredient
        fields = ('id', 'amount',)


class IngredientSerializer(serializers.ModelSerializer):
    amount = RecipeIngredientSerializer(read_only=True)

    class Meta:
        model = Ingredient
        fields = '__all__'


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
        model = Recipes
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
        model = Recipes
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text',
                  'cooking_time')

    def recipes_bulk_create(self, recipe, ingredients):
        RecipesIngredient.objects.bulk_create(RecipesIngredient(
            recipe=recipe,
            ingredient=ingredient.get('ingredient'),
            amount=ingredient.get('amount'),)
            for ingredient in ingredients)

    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe = Recipes.objects.create(
            author=self.context.get('request').user,
            image=validated_data.pop('image'),
            name=validated_data.pop('name'),
            text=validated_data.pop('text'),
            cooking_time=validated_data.pop('cooking_time'), )
        recipe.tags.set(tags)
        self.recipes_bulk_create(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = validated_data.pop('recipe_ingredients', [])
        tags = validated_data.pop('tags', [])
        instance.tags.set(tags)
        self.recipes_bulk_create(instance, ingredients)
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
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')


class BaseFavoriteAndShopCartSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        fields = ('id', )

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
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')
