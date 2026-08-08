import django.db.models.deletion
from django.db import migrations, models


LEGACY_TO_SLUG = {
    'super_admin': 'super-admin',
    'admin': 'administrator',
    'content_editor': 'content-editor',
    'client_user': 'client-user',
}


def migrate_role_values(apps, schema_editor):
    Profile = apps.get_model('users', 'Profile')
    Role = apps.get_model('roles', 'Role')
    roles_by_slug = {r.slug: r for r in Role.objects.all()}
    for profile in Profile.objects.all():
        slug = LEGACY_TO_SLUG.get(profile.role)
        profile.role_new_id = roles_by_slug[slug].id if slug in roles_by_slug else None
        profile.save(update_fields=['role_new'])


def reverse_role_values(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('roles', '0002_seed_system_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='role_new',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='profiles',
                to='roles.role',
            ),
        ),
        migrations.RunPython(migrate_role_values, reverse_role_values),
        migrations.RemoveField(
            model_name='profile',
            name='role',
        ),
        migrations.RenameField(
            model_name='profile',
            old_name='role_new',
            new_name='role',
        ),
    ]
