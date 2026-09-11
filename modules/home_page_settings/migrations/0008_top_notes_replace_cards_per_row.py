from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_page_settings', '0007_asset_class_cards_default_5'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepagesettings',
            name='top_notes_latest_research',
            field=models.PositiveSmallIntegerField(
                choices=[(3, 'Top 3'), (6, 'Top 6'), (9, 'Top 9'), (10, 'Top 10'), (12, 'Top 12'), (15, 'Top 15'), (20, 'Top 20')],
                default=6,
            ),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='top_notes_weekly_notes',
            field=models.PositiveSmallIntegerField(
                choices=[(3, 'Top 3'), (6, 'Top 6'), (9, 'Top 9'), (10, 'Top 10'), (12, 'Top 12'), (15, 'Top 15'), (20, 'Top 20')],
                default=6,
            ),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='top_notes_monthly_notes',
            field=models.PositiveSmallIntegerField(
                choices=[(3, 'Top 3'), (6, 'Top 6'), (9, 'Top 9'), (10, 'Top 10'), (12, 'Top 12'), (15, 'Top 15'), (20, 'Top 20')],
                default=6,
            ),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='top_notes_quarterly_notes',
            field=models.PositiveSmallIntegerField(
                choices=[(3, 'Top 3'), (6, 'Top 6'), (9, 'Top 9'), (10, 'Top 10'), (12, 'Top 12'), (15, 'Top 15'), (20, 'Top 20')],
                default=6,
            ),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='top_notes_annual_notes',
            field=models.PositiveSmallIntegerField(
                choices=[(3, 'Top 3'), (6, 'Top 6'), (9, 'Top 9'), (10, 'Top 10'), (12, 'Top 12'), (15, 'Top 15'), (20, 'Top 20')],
                default=6,
            ),
        ),
        migrations.RemoveField(
            model_name='homepagesettings',
            name='cards_per_row_featured_research',
        ),
        migrations.RemoveField(
            model_name='homepagesettings',
            name='cards_per_row_latest_research',
        ),
        migrations.RemoveField(
            model_name='homepagesettings',
            name='cards_per_row_weekly_notes',
        ),
        migrations.RemoveField(
            model_name='homepagesettings',
            name='cards_per_row_monthly_notes',
        ),
        migrations.RemoveField(
            model_name='homepagesettings',
            name='cards_per_row_quarterly_notes',
        ),
        migrations.RemoveField(
            model_name='homepagesettings',
            name='cards_per_row_annual_notes',
        ),
        migrations.RemoveField(
            model_name='homepagesettings',
            name='cards_per_row_research_by_asset_class',
        ),
    ]
