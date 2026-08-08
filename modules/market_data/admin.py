from django.contrib import admin

from .models import MarketInstrument


@admin.register(MarketInstrument)
class MarketInstrumentAdmin(admin.ModelAdmin):
    list_display = ('label', 'symbol', 'last_price', 'last_updated', 'is_active')
    search_fields = ('label', 'symbol')
