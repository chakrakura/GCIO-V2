from django.db import migrations, models


CARDS_PER_ROW_FIELDS = (
    'cards_per_row_featured_research',
    'cards_per_row_latest_research',
    'cards_per_row_weekly_notes',
    'cards_per_row_monthly_notes',
    'cards_per_row_quarterly_notes',
    'cards_per_row_annual_notes',
    'cards_per_row_research_by_asset_class',
)

CHOICES = [(n, str(n)) for n in range(1, 11)]


def copy_global_cards_per_row(apps, schema_editor):
    HomePageSettings = apps.get_model('home_page_settings', 'HomePageSettings')
    for obj in HomePageSettings.objects.all():
        value = getattr(obj, 'cards_per_row', 2) or 2
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 2
        if value not in range(1, 11):
            value = 2
        for field in CARDS_PER_ROW_FIELDS:
            setattr(obj, field, value)
        obj.save(update_fields=list(CARDS_PER_ROW_FIELDS))


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('home_page_settings', '0005_cards_per_row'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepagesettings',
            name='cards_per_row_featured_research',
            field=models.PositiveSmallIntegerField(choices=CHOICES, default=2),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='cards_per_row_latest_research',
            field=models.PositiveSmallIntegerField(choices=CHOICES, default=2),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='cards_per_row_weekly_notes',
            field=models.PositiveSmallIntegerField(choices=CHOICES, default=2),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='cards_per_row_monthly_notes',
            field=models.PositiveSmallIntegerField(choices=CHOICES, default=2),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='cards_per_row_quarterly_notes',
            field=models.PositiveSmallIntegerField(choices=CHOICES, default=2),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='cards_per_row_annual_notes',
            field=models.PositiveSmallIntegerField(choices=CHOICES, default=2),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='cards_per_row_research_by_asset_class',
            field=models.PositiveSmallIntegerField(choices=CHOICES, default=2),
        ),
        migrations.RunPython(copy_global_cards_per_row, noop),
        migrations.RemoveField(
            model_name='homepagesettings',
            name='cards_per_row',
        ),
    ]
