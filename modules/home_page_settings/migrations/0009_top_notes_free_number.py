from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_page_settings', '0008_top_notes_replace_cards_per_row'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homepagesettings',
            name='top_notes_latest_research',
            field=models.PositiveSmallIntegerField(default=6),
        ),
        migrations.AlterField(
            model_name='homepagesettings',
            name='top_notes_weekly_notes',
            field=models.PositiveSmallIntegerField(default=6),
        ),
        migrations.AlterField(
            model_name='homepagesettings',
            name='top_notes_monthly_notes',
            field=models.PositiveSmallIntegerField(default=6),
        ),
        migrations.AlterField(
            model_name='homepagesettings',
            name='top_notes_quarterly_notes',
            field=models.PositiveSmallIntegerField(default=6),
        ),
        migrations.AlterField(
            model_name='homepagesettings',
            name='top_notes_annual_notes',
            field=models.PositiveSmallIntegerField(default=6),
        ),
    ]
