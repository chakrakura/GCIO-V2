from django.db import models
from django.utils.text import slugify


class TaxonomyTerm(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AssetClass(TaxonomyTerm):
    show_on_home = models.BooleanField(
        default=True, help_text='Show in the "Research by Asset Class" section on the client home page.'
    )

    class Meta:
        db_table = 'taxonomy_asset_class'
        ordering = ['name']


class CountryRegion(TaxonomyTerm):
    class Meta:
        db_table = 'taxonomy_country_region'
        ordering = ['name']


class PublicationType(TaxonomyTerm):
    show_on_home = models.BooleanField(
        default=True, help_text='Show in the "Regular Publications" section on the client home page.'
    )
    series_name = models.CharField(
        max_length=150, blank=True,
        help_text='Display title for the series page, e.g. "The GCIO Daily". Defaults to the name above if left blank.'
    )
    cadence_label = models.CharField(
        max_length=100, blank=True, help_text='How often it publishes, e.g. "Every trading day". Optional.'
    )
    description = models.TextField(blank=True, help_text='Shown on the series page header. Optional.')

    class Meta:
        db_table = 'taxonomy_publication_type'
        ordering = ['name']

    def display_name(self):
        return self.series_name or self.name


class ReportTag(TaxonomyTerm):
    class Meta:
        db_table = 'taxonomy_report_tag'
        ordering = ['name']
