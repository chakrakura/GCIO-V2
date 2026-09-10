from django.db import models


class HomePageSettings(models.Model):
    """Singleton controlling which sections appear on the client /portal Home page."""

    show_featured_research = models.BooleanField(default=True)
    show_latest_research = models.BooleanField(default=True)
    show_weekly_notes = models.BooleanField(default=True)
    show_monthly_notes = models.BooleanField(default=True)
    show_quarterly_notes = models.BooleanField(default=True)
    show_annual_notes = models.BooleanField(default=True)
    show_special_reports = models.BooleanField(default=True)
    show_regular_publications = models.BooleanField(default=True)
    show_research_by_asset_class = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Home page settings'
        verbose_name_plural = 'Home page settings'

    def __str__(self):
        return 'Home page settings'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
