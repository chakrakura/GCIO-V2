from django.db import models


class MarketInstrument(models.Model):
    VALUE_INDEX = 'index'
    VALUE_PERCENT = 'percent'
    VALUE_CURRENCY = 'currency'
    VALUE_FORMAT_CHOICES = [
        (VALUE_INDEX, 'Plain number (e.g. 5,123.41)'),
        (VALUE_PERCENT, 'Percent (e.g. 4.42%)'),
        (VALUE_CURRENCY, 'Currency (e.g. $113.20)'),
    ]

    CHANGE_PERCENT = 'percent'
    CHANGE_BP = 'bp'
    CHANGE_FORMAT_CHOICES = [
        (CHANGE_PERCENT, 'Percent change (e.g. -0.4%)'),
        (CHANGE_BP, 'Basis points (e.g. +3 bp) — for yields'),
    ]

    label = models.CharField(max_length=50, help_text='Display name, e.g. "S&P 500".')
    symbol = models.CharField(
        max_length=20, unique=True, help_text='Yahoo Finance ticker symbol, e.g. "^GSPC", "GC=F".'
    )
    value_format = models.CharField(max_length=10, choices=VALUE_FORMAT_CHOICES, default=VALUE_INDEX)
    change_format = models.CharField(max_length=10, choices=CHANGE_FORMAT_CHOICES, default=CHANGE_PERCENT)
    decimal_places = models.PositiveSmallIntegerField(default=2)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, help_text='Show in the client portal ticker.')
    is_hero_stat = models.BooleanField(
        default=False, help_text='Also show as one of the 2 stat tiles on the Featured Research hero card.'
    )

    last_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    last_change = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    last_change_percent = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'market_instruments'
        ordering = ['display_order', 'label']

    def __str__(self):
        return self.label

    @property
    def is_up(self):
        if self.last_change is None:
            return None
        return self.last_change >= 0

    @property
    def formatted_value(self):
        if self.last_price is None:
            return '—'
        text = f'{self.last_price:,.{self.decimal_places}f}'
        if self.value_format == self.VALUE_PERCENT:
            return f'{text}%'
        if self.value_format == self.VALUE_CURRENCY:
            return f'${text}'
        return text

    @property
    def formatted_change(self):
        sign = '+' if self.is_up else ''
        if self.change_format == self.CHANGE_BP:
            if self.last_change is None:
                return '—'
            bp = round(self.last_change * 100)
            return f'{"+" if bp >= 0 else ""}{bp} bp'
        if self.last_change_percent is None:
            return '—'
        return f'{sign}{self.last_change_percent:.1f}%'

    def as_ticker_tuple(self):
        """(label, value, change, is_up) — matches the shape client_portal templates expect."""
        return (self.label, self.formatted_value, self.formatted_change, bool(self.is_up))
