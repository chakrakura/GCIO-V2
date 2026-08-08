from django.contrib import admin

from .models import ActivityLog, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role', 'organizations')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'target')
    list_filter = ('actor',)
    search_fields = ('action', 'target', 'actor__username', 'actor__email')
    date_hierarchy = 'created_at'
