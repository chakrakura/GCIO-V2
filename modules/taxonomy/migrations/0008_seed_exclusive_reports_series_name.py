from django.db import migrations


def seed_exclusive_reports(apps, schema_editor):
    PublicationType = apps.get_model('taxonomy', 'PublicationType')
    PublicationType.objects.filter(slug='special-report').update(
        series_name='Exclusive Reports',
        description='In-depth, high-conviction research reserved for special situations — structural shifts, thematic deep dives, and calls the desk feels strongly enough about to publish outside the regular cadence.',
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0007_seed_publication_series_fields'),
    ]

    operations = [
        migrations.RunPython(seed_exclusive_reports, noop),
    ]
