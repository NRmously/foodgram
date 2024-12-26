from django.urls import include, path

from rest_framework.routers import DefaultRouter

from api.views import (AvatarPutDeleteView, IngredientsViewSet, RecipViewSet,
                       SubcribeView, SubscribeListView, TagsViewSet,
                       UserMeViewSet)

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('tags', TagsViewSet)
router_v1.register('ingredients', IngredientsViewSet)
router_v1.register(r'recipes', RecipViewSet, basename='recipes')

urlpatterns = [
    path('users/me/', UserMeViewSet.as_view({'get': 'me'}), name='user-me'),
    path('users/subscriptions/', SubscribeListView.as_view()),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/avatar/', AvatarPutDeleteView.as_view()),
    path('users/<int:pk>/subscribe/', SubcribeView.as_view()),
]
