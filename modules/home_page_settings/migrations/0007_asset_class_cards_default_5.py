from django.db import migrations, models


def set_research_by_asset_class_cards_default(apps, schema_editor):
    HomePageSettings = apps.get_model('home_page_settings', 'HomePageSettings')
    HomePageSettings.objects.all().update(cards_per_row_research_by_asset_class=5)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('home_page_settings', '0006_section_cards_per_row'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homepagesettings',
            name='cards_per_row_research_by_asset_class',
            field=models.PositiveSmallIntegerField(
                choices=[(n, str(n)) for n in range(1, 11)],
                default=5,
            ),
        ),
        migrations.RunPython(set_research_by_asset_class_cards_default, noop),
    ]
