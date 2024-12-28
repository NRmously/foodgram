from django.contrib import admin

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')


class RecipesIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipesAdmin(admin.ModelAdmin):
    inlines = [RecipesIngredientInline]
    list_display = ('name', 'author', 'sum_favorites')
    search_fields = ('name',)
    list_filter = ('tags', 'author')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('author')
        queryset = queryset.prefetch_related('tags', 'ingredients', 'favorite')
        return queryset

    def sum_favorites(self, obj):
        return obj.favorite.count()
    sum_favorites.short_description = 'Кол-во в избранном'


@admin.register(RecipeIngredient)
class RecipesIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe')
