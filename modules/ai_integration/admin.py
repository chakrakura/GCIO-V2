from django.contrib import admin

from .models import AIGenerationDefaults, AIProviderConfig


@admin.register(AIProviderConfig)
class AIProviderConfigAdmin(admin.ModelAdmin):
    list_display = ('provider', 'is_connected', 'default_model', 'last_tested_at')


@admin.register(AIGenerationDefaults)
class AIGenerationDefaultsAdmin(admin.ModelAdmin):
    list_display = ('default_provider', 'default_report_size', 'temperature', 'updated_at')
