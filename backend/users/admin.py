from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from users.models import Subscribers, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'avatar',
                    'is_active')
    search_fields = ('email', 'username')
    list_filter = ('is_active', 'date_joined')
    list_per_page = 25
    fields = ('email', 'username', 'first_name', 'last_name', 'avatar',
              'is_active')
    readonly_fields = ('date_joined',)


@admin.register(Subscribers)
class SubscribersAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'subscribe_to', 'created_at')
    search_fields = ('subscriber__email', 'subscribe_to__email')
    list_filter = ('subscribe_to',)
    list_editable = ('subscribe_to',)
    list_per_page = 20
    fields = ('subscriber', 'subscribe_to', 'created_at')
    readonly_fields = ('created_at',)


admin.site.unregister(Group)
