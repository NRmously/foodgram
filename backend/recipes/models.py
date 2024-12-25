from django.db import models

from users.models import User

from .constants import (MAX_INGREDIENT_MEASURE_UNIT_LENGTH,
                        MAX_INGREDIENT_NAME_LENGTH, MAX_RECIPE_NAME_LENGTH,
                        MAX_TAG_NAME_LENGTH, MAX_TAG_SLUG_LENGTH)
from .validators import (amount_validator, cooking_time_validator,
                         tag_regex_validator)


class Tag(models.Model):
    name = models.CharField('Название', max_length=MAX_TAG_NAME_LENGTH,
                            unique=True, blank=False)
    slug = models.SlugField('Slug', max_length=MAX_TAG_SLUG_LENGTH,
                            unique=True, blank=False,
                            validators=(tag_regex_validator,))

    class Meta:
        verbose_name, verbose_name_plural = 'Тег', 'Теги'

    def __str__(self) -> str:
        return (f'{self.name} {self.slug}')


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=MAX_INGREDIENT_NAME_LENGTH,
                            blank=False, unique=True)
    measurement_unit = models.CharField(
        'Ед. измерения',
        max_length=MAX_INGREDIENT_MEASURE_UNIT_LENGTH,
        blank=False
    )

    class Meta:
        verbose_name, verbose_name_plural = 'Ингредиент', 'Ингредиенты'

    def __str__(self) -> str:
        return (f'{self.name} {self.measurement_unit}')


class Recipes(models.Model):
    tags = models.ManyToManyField(Tag, related_name='recipes',
                                  verbose_name='Тег')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name='Автор',)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipesIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    name = models.CharField('Название',
                            max_length=MAX_RECIPE_NAME_LENGTH,
                            blank=False)
    image = models.ImageField('Картинка', upload_to='recipes/images/',
                              blank=False)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время готовки',
        validators=cooking_time_validator
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name, verbose_name_plural = 'Рецепт', 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return self.name


class RecipesIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='recipeingredients',
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipeingredients',
        verbose_name='Ингредиент')
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=amount_validator
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='unique_recipes'),
        ]

    def __str__(self):
        return (f'{self.recipe.name}: '
                f'{self.ingredient.name} - '
                f'{self.amount} '
                f'{self.ingredient.measurement_unit}')


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепт')

    class Meta:
        verbose_name, verbose_name_plural = 'Избранное', 'Избранное'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_favorites'),
        ]

    def __str__(self) -> str:
        return f'{self.user} добавил {self.recipe} в избранное'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopcart',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='shopcart',
        verbose_name='Рецепт')

    class Meta:
        verbose_name, verbose_name_plural = 'Корзина', 'Корзина'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shop_cart'),
        ]

    def __str__(self) -> str:
        return f'{self.user} добавил {self.recipe} в корзину'
