from django.conf import settings
from django.db import models

from modules.organizations.models import Organization
from modules.taxonomy.models import AssetClass, CountryRegion, PublicationType, ReportTag


class Report(models.Model):
    CONTENT_TEXT = 'text'
    CONTENT_PDF = 'pdf'
    CONTENT_PRESENTATION = 'presentation'
    CONTENT_TYPE_CHOICES = [
        (CONTENT_TEXT, 'Article'),
        (CONTENT_PDF, 'PDF'),
        (CONTENT_PRESENTATION, 'Presentation'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    ACCESS_ALL = 'all'
    ACCESS_SELECTED = 'selected'
    ACCESS_CHOICES = [
        (ACCESS_ALL, 'All users'),
        (ACCESS_SELECTED, 'Selected organisations'),
    ]

    content_type = models.CharField(max_length=15, choices=CONTENT_TYPE_CHOICES, default=CONTENT_TEXT)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    body = models.TextField(blank=True)
    file_upload = models.FileField(upload_to='reports/uploads/', blank=True, null=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    access_level = models.CharField(max_length=10, choices=ACCESS_CHOICES, default=ACCESS_ALL)
    visible_organizations = models.ManyToManyField(Organization, blank=True, related_name='visible_reports')
    page_count = models.PositiveIntegerField(default=1)
    is_featured = models.BooleanField(
        default=False, help_text='Show in the Featured Research section on the client portal home page.'
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports'
    )
    publication_type = models.ForeignKey(
        PublicationType, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports'
    )
    asset_classes = models.ManyToManyField(AssetClass, blank=True, related_name='reports')
    countries_regions = models.ManyToManyField(CountryRegion, blank=True, related_name='reports')
    tags = models.ManyToManyField(ReportTag, blank=True, related_name='reports')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class SavedReport(models.Model):
    """A client user bookmarking a report for later — powers the portal's Saved Reports page."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_reports')
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_reports'
        unique_together = ('user', 'report')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} saved "{self.report}"'
