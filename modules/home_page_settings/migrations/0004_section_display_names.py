from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_page_settings', '0003_show_special_reports'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepagesettings',
            name='title_annual_notes',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='title_featured_research',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='title_latest_research',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='title_monthly_notes',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='title_quarterly_notes',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='title_research_by_asset_class',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='homepagesettings',
            name='title_weekly_notes',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
    ]
