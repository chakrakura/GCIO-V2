from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_page_settings', '0004_section_display_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepagesettings',
            name='cards_per_row',
            field=models.PositiveSmallIntegerField(
                choices=[(2, '2'), (3, '3'), (4, '4'), (5, '5')],
                default=2,
            ),
        ),
    ]
