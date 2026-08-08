from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'publication_type', 'created_at')
    list_filter = ('status', 'publication_type')
    search_fields = ('title', 'description')
