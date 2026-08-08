from django.db import migrations

INSTRUMENTS = [
    {
        'label': 'S&P 500', 'symbol': '^GSPC', 'value_format': 'index', 'change_format': 'percent',
        'decimal_places': 2, 'display_order': 1, 'is_hero_stat': True,
    },
    {
        'label': 'US 10Y', 'symbol': '^TNX', 'value_format': 'percent', 'change_format': 'bp',
        'decimal_places': 2, 'display_order': 2, 'is_hero_stat': False,
    },
    {
        'label': 'US 30Y', 'symbol': '^TYX', 'value_format': 'percent', 'change_format': 'bp',
        'decimal_places': 2, 'display_order': 3, 'is_hero_stat': False,
    },
    {
        'label': 'BRENT', 'symbol': 'BZ=F', 'value_format': 'currency', 'change_format': 'percent',
        'decimal_places': 2, 'display_order': 4, 'is_hero_stat': False,
    },
    {
        'label': 'GOLD', 'symbol': 'GC=F', 'value_format': 'currency', 'change_format': 'percent',
        'decimal_places': 0, 'display_order': 5, 'is_hero_stat': True,
    },
    {
        'label': 'DXY', 'symbol': 'DX-Y.NYB', 'value_format': 'index', 'change_format': 'percent',
        'decimal_places': 1, 'display_order': 6, 'is_hero_stat': False,
    },
]


def seed_instruments(apps, schema_editor):
    MarketInstrument = apps.get_model('market_data', 'MarketInstrument')
    for data in INSTRUMENTS:
        MarketInstrument.objects.get_or_create(symbol=data['symbol'], defaults=data)


def remove_instruments(apps, schema_editor):
    MarketInstrument = apps.get_model('market_data', 'MarketInstrument')
    MarketInstrument.objects.filter(symbol__in=[i['symbol'] for i in INSTRUMENTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('market_data', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_instruments, remove_instruments),
    ]
