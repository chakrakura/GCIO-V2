from django.db import migrations, models


def copy_organization_to_m2m(apps, schema_editor):
    Profile = apps.get_model('users', 'Profile')
    for profile in Profile.objects.exclude(organization__isnull=True):
        profile.organizations_new.add(profile.organization_id)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0004_alter_organization_table'),
        ('users', '0005_profile_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='organizations_new',
            field=models.ManyToManyField(blank=True, related_name='members_new', to='organizations.organization'),
        ),
        migrations.RunPython(copy_organization_to_m2m, noop_reverse),
        migrations.RemoveField(
            model_name='profile',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='report_access',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='selected_organizations',
        ),
        migrations.RenameField(
            model_name='profile',
            old_name='organizations_new',
            new_name='organizations',
        ),
        migrations.AlterField(
            model_name='profile',
            name='organizations',
            field=models.ManyToManyField(blank=True, related_name='members', to='organizations.organization'),
        ),
    ]
