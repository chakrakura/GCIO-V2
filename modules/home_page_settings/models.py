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

CARDS_PER_ROW_MIN = 1
CARDS_PER_ROW_MAX = 10
CARDS_PER_ROW_DEFAULT = 2
CARDS_PER_ROW_CHOICES = tuple(
    (n, str(n)) for n in range(CARDS_PER_ROW_MIN, CARDS_PER_ROW_MAX + 1)
)
CARDS_PER_ROW_FIELD_BY_TOGGLE = {
    'show_featured_research': 'cards_per_row_featured_research',
    'show_latest_research': 'cards_per_row_latest_research',
    'show_weekly_notes': 'cards_per_row_weekly_notes',
    'show_monthly_notes': 'cards_per_row_monthly_notes',
    'show_quarterly_notes': 'cards_per_row_quarterly_notes',
    'show_annual_notes': 'cards_per_row_annual_notes',
    'show_research_by_asset_class': 'cards_per_row_research_by_asset_class',
}
CARDS_PER_ROW_FIELDS = tuple(
    CARDS_PER_ROW_FIELD_BY_TOGGLE[toggle] for toggle, _, _ in SECTION_HEADINGS
)


def normalize_cards_per_row(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return CARDS_PER_ROW_DEFAULT
    if CARDS_PER_ROW_MIN <= value <= CARDS_PER_ROW_MAX:
        return value
    return CARDS_PER_ROW_DEFAULT


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

    cards_per_row_featured_research = models.PositiveSmallIntegerField(
        default=CARDS_PER_ROW_DEFAULT, choices=CARDS_PER_ROW_CHOICES,
    )
    cards_per_row_latest_research = models.PositiveSmallIntegerField(
        default=CARDS_PER_ROW_DEFAULT, choices=CARDS_PER_ROW_CHOICES,
    )
    cards_per_row_weekly_notes = models.PositiveSmallIntegerField(
        default=CARDS_PER_ROW_DEFAULT, choices=CARDS_PER_ROW_CHOICES,
    )
    cards_per_row_monthly_notes = models.PositiveSmallIntegerField(
        default=CARDS_PER_ROW_DEFAULT, choices=CARDS_PER_ROW_CHOICES,
    )
    cards_per_row_quarterly_notes = models.PositiveSmallIntegerField(
        default=CARDS_PER_ROW_DEFAULT, choices=CARDS_PER_ROW_CHOICES,
    )
    cards_per_row_annual_notes = models.PositiveSmallIntegerField(
        default=CARDS_PER_ROW_DEFAULT, choices=CARDS_PER_ROW_CHOICES,
    )
    cards_per_row_research_by_asset_class = models.PositiveSmallIntegerField(
        default=5, choices=CARDS_PER_ROW_CHOICES,
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

    def cards_per_row_for(self, field):
        return normalize_cards_per_row(getattr(self, field, CARDS_PER_ROW_DEFAULT))

    def cards_per_row_for_toggle(self, toggle_field):
        return self.cards_per_row_for(CARDS_PER_ROW_FIELD_BY_TOGGLE[toggle_field])
