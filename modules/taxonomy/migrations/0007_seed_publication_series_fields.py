from django.db import migrations

SERIES_DEFAULTS = {
    'daily-note': ('The GCIO Daily', 'Every trading day', 'A concise morning briefing on overnight moves across rates, equities, commodities and FX, with the desk’s read on what matters.'),
    'weekly-insight': ('The GCIO Weekly', 'Every Monday', 'One theme, developed in depth — the single idea we think is most worth a professional investor’s time this week.'),
    'monthly-digest': ('The GCIO Monthly', 'First business day', 'The full cross-asset review: what happened, what we changed, and how the house is positioned into the month ahead.'),
}


def seed_series_fields(apps, schema_editor):
    PublicationType = apps.get_model('taxonomy', 'PublicationType')
    for slug, (series_name, cadence_label, description) in SERIES_DEFAULTS.items():
        PublicationType.objects.filter(slug=slug).update(
            series_name=series_name, cadence_label=cadence_label, description=description,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0006_publicationtype_cadence_label_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_series_fields, noop),
    ]
