from django.db import migrations, models


def seed_defaults(apps, schema_editor):
    HomePageSettings = apps.get_model('home_page_settings', 'HomePageSettings')
    HomePageSettings.objects.get_or_create(
        pk=1,
        defaults={
            'show_featured_research': True,
            'show_latest_research': True,
            'show_regular_publications': True,
            'show_research_by_asset_class': True,
        },
    )


def unseed_defaults(apps, schema_editor):
    HomePageSettings = apps.get_model('home_page_settings', 'HomePageSettings')
    HomePageSettings.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HomePageSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('show_featured_research', models.BooleanField(default=True)),
                ('show_latest_research', models.BooleanField(default=True)),
                ('show_regular_publications', models.BooleanField(default=True)),
                ('show_research_by_asset_class', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Home page settings',
                'verbose_name_plural': 'Home page settings',
            },
        ),
        migrations.RunPython(seed_defaults, unseed_defaults),
    ]
