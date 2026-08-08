from django.contrib import admin

from .models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_internal', 'is_system', 'can_manage_users', 'can_manage_roles', 'can_manage_organizations', 'can_manage_content')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
