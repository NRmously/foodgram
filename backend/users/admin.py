from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from users.models import Subscribers, User


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'avatar')
    search_fields = ('email', 'username')


class SubscribersAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'subscribe_to')


admin.site.register(User, CustomUserAdmin)
admin.site.register(Subscribers, SubscribersAdmin)
admin.site.unregister(Group)
