import io

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.constants import (FONT_SIZE, SHOPPING_CART_OFFSET_X,
                           SHOPPING_CART_OFFSET_Y, SHOPPING_CART_X_SIZE)
from api.filters import IngredientsNameFilter, RecipeFilter
from api.permissions import IsOwnerOrReadOnly
from recipes.models import (Favorite, Ingredient, Recipes, RecipesIngredient,
                            ShoppingCart, Tag)

from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeSerializer,
                          ShopCartSerializer, TagSerializer)


class TagsViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientsNameFilter
    pagination_class = None


class RecipViewSet(ModelViewSet):
    queryset = Recipes.objects.select_related('author').prefetch_related(
        'tags', 'recipeingredients__ingredient'
    )
    serializer_class = RecipeSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def show_short_link(self, request, pk):
        return redirect(f'/recipes/{pk}/')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def post_request_processing(self, request, model, serializer_class, pk):
        recipe = get_object_or_404(Recipes, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete_request_processing(self, request, model, serializer, pk):
        recipe = get_object_or_404(Recipes, id=pk)
        serializer = serializer(recipe)
        deleted, _ = model.objects.filter(user=request.user, recipe=recipe
                                          ).delete()
        if deleted > 0:
            return Response(
                {'Сообщение': f'Рецепт удален из {model._meta.verbose_name}!'},
                status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'Ошибка': f'Рецепт не найден в {model._meta.verbose_name}'},
                status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['GET'],
        permission_classes=(AllowAny, ),
        url_path='get-link'
    )
    def get_link(self, request, pk):
        recipe = get_object_or_404(Recipes, id=pk)
        shortlink = request.build_absolute_uri(f'/s/{recipe.id}')
        return Response({'short-link': shortlink}, status=status.HTTP_200_OK)

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=(IsAuthenticated, IsOwnerOrReadOnly),
        serializer_class=FavoriteSerializer
    )
    def favorite(self, request, pk):
        return self.post_request_processing(request, Favorite,
                                            FavoriteSerializer, pk)

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        return self.delete_request_processing(request, Favorite,
                                              FavoriteSerializer, pk)

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=(IsAuthenticated, IsOwnerOrReadOnly),
        serializer_class=ShopCartSerializer, url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        return self.post_request_processing(request, ShoppingCart,
                                            ShopCartSerializer, pk)

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        return self.delete_request_processing(request, ShoppingCart,
                                              ShopCartSerializer, pk)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthenticated, ),
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipesIngredient.objects
            .filter(recipe__shopcart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        p.setFont('DejaVuSans', FONT_SIZE)
        p.drawString(SHOPPING_CART_X_SIZE, height - SHOPPING_CART_OFFSET_X,
                     'Список покупок:')
        y_position = height - SHOPPING_CART_OFFSET_Y
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            total_amount = ingredient['total_amount']
            key = f'{name} ({measurement_unit})'
            p.drawString(SHOPPING_CART_X_SIZE, y_position,
                         f"{key} — {total_amount}")
            y_position -= 20
        p.showPage()
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_cart.pdf"')
        return response
