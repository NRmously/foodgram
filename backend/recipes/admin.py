from django.contrib import admin

from recipes.models import (Favorite, Ingredient, Recipes, RecipesIngredient,
                            ShoppingCart, Tag)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')


class RecipesIngredientInline(admin.TabularInline):
    model = RecipesIngredient
    extra = 1


class RecipesAdmin(admin.ModelAdmin):
    inlines = [RecipesIngredientInline]
    list_display = ('name', 'author', 'sum_favorites')
    search_fields = ('name',)
    list_filter = ('tags',)

    def sum_favorites(self, obj):
        return obj.favorite.count()
    sum_favorites.short_description = 'Кол-во в избранном'


class RecipesIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


class Shopping_cart_Admin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipes, RecipesAdmin)
admin.site.register(RecipesIngredient, RecipesIngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, Shopping_cart_Admin)
