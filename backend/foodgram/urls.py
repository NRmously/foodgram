from django.contrib import admin
from django.urls import include, path

from api.views import RecipViewSet

urlpatterns = [
    path('s/<int:pk>/',
         RecipViewSet.as_view({'get': 'show_short_link'}),
         name='shortlink'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
