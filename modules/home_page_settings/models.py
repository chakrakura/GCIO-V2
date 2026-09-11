from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

HEADING_MAX_LENGTH = 80

# Toggle field, stored display-name field, default heading shown on /portal.
SECTION_HEADINGS = (
    ('show_featured_research', 'title_featured_research', 'Featured Research'),
    ('show_latest_research', 'title_latest_research', 'Daily Note'),
    ('show_weekly_notes', 'title_weekly_notes', 'Weekly Insight'),
    ('show_monthly_notes', 'title_monthly_notes', 'Monthly Digest'),
    ('show_quarterly_notes', 'title_quarterly_notes', 'Quarterly Review'),
    ('show_annual_notes', 'title_annual_notes', 'Annual Outlook'),
    ('show_research_by_asset_class', 'title_research_by_asset_class', 'Research by Asset Class'),
)

TITLE_FIELDS = tuple(title_field for _, title_field, _ in SECTION_HEADINGS)
DEFAULT_HEADING_BY_TOGGLE = {toggle: default for toggle, _, default in SECTION_HEADINGS}
TITLE_FIELD_BY_TOGGLE = {toggle: title_field for toggle, title_field, _ in SECTION_HEADINGS}
DEFAULT_HEADING_BY_TITLE_FIELD = {title_field: default for _, title_field, default in SECTION_HEADINGS}

TOP_NOTES_DEFAULT = 6
TOP_NOTES_MIN = 1
TOP_NOTES_MAX = 50
TOP_NOTES_FIELD_BY_TOGGLE = {
    'show_latest_research': 'top_notes_latest_research',
    'show_weekly_notes': 'top_notes_weekly_notes',
    'show_monthly_notes': 'top_notes_monthly_notes',
    'show_quarterly_notes': 'top_notes_quarterly_notes',
    'show_annual_notes': 'top_notes_annual_notes',
}
TOP_NOTES_FIELDS = tuple(TOP_NOTES_FIELD_BY_TOGGLE.values())


def normalize_top_notes(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return TOP_NOTES_DEFAULT
    if TOP_NOTES_MIN <= value <= TOP_NOTES_MAX:
        return value
    return TOP_NOTES_DEFAULT


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

    title_featured_research = models.CharField(max_length=HEADING_MAX_LENGTH, blank=True, default='')
    title_latest_research = models.CharField(max_length=HEADING_MAX_LENGTH, blank=True, default='')
    title_weekly_notes = models.CharField(max_length=HEADING_MAX_LENGTH, blank=True, default='')
    title_monthly_notes = models.CharField(max_length=HEADING_MAX_LENGTH, blank=True, default='')
    title_quarterly_notes = models.CharField(max_length=HEADING_MAX_LENGTH, blank=True, default='')
    title_annual_notes = models.CharField(max_length=HEADING_MAX_LENGTH, blank=True, default='')
    title_research_by_asset_class = models.CharField(max_length=HEADING_MAX_LENGTH, blank=True, default='')

    top_notes_latest_research = models.PositiveSmallIntegerField(
        default=TOP_NOTES_DEFAULT,
        validators=[MinValueValidator(TOP_NOTES_MIN), MaxValueValidator(TOP_NOTES_MAX)],
    )
    top_notes_weekly_notes = models.PositiveSmallIntegerField(
        default=TOP_NOTES_DEFAULT,
        validators=[MinValueValidator(TOP_NOTES_MIN), MaxValueValidator(TOP_NOTES_MAX)],
    )
    top_notes_monthly_notes = models.PositiveSmallIntegerField(
        default=TOP_NOTES_DEFAULT,
        validators=[MinValueValidator(TOP_NOTES_MIN), MaxValueValidator(TOP_NOTES_MAX)],
    )
    top_notes_quarterly_notes = models.PositiveSmallIntegerField(
        default=TOP_NOTES_DEFAULT,
        validators=[MinValueValidator(TOP_NOTES_MIN), MaxValueValidator(TOP_NOTES_MAX)],
    )
    top_notes_annual_notes = models.PositiveSmallIntegerField(
        default=TOP_NOTES_DEFAULT,
        validators=[MinValueValidator(TOP_NOTES_MIN), MaxValueValidator(TOP_NOTES_MAX)],
    )

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

    def heading_for_title_field(self, title_field):
        stored = (getattr(self, title_field, '') or '').strip()
        return stored or DEFAULT_HEADING_BY_TITLE_FIELD[title_field]

    def heading_for_toggle(self, toggle_field):
        return self.heading_for_title_field(TITLE_FIELD_BY_TOGGLE[toggle_field])

    @property
    def featured_research_heading(self):
        return self.heading_for_toggle('show_featured_research')

    @property
    def research_by_asset_class_heading(self):
        return self.heading_for_toggle('show_research_by_asset_class')

    def top_notes_for(self, field):
        return normalize_top_notes(getattr(self, field, TOP_NOTES_DEFAULT))

    def top_notes_for_toggle(self, toggle_field):
        field = TOP_NOTES_FIELD_BY_TOGGLE.get(toggle_field)
        if not field:
            return TOP_NOTES_DEFAULT
        return self.top_notes_for(field)
