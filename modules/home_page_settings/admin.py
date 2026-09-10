from django.contrib import admin

from .models import HomePageSettings


@admin.register(HomePageSettings)
class HomePageSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'show_featured_research',
        'show_latest_research',
        'show_weekly_notes',
        'show_monthly_notes',
        'show_quarterly_notes',
        'show_annual_notes',
        'show_special_reports',
        'show_research_by_asset_class',
        'updated_at',
    )
