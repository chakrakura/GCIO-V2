from django.contrib import admin

from .models import AssetClass, CountryRegion, PublicationType, ReportTag


@admin.register(AssetClass)
class AssetClassAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(CountryRegion)
class CountryRegionAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(PublicationType)
class PublicationTypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(ReportTag)
class ReportTagAdmin(admin.ModelAdmin):
    search_fields = ('name',)
