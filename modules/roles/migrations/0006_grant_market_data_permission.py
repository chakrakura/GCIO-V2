from django.db import migrations

GRANTED_SLUGS = ['super-admin', 'administrator']


def grant_permission(apps, schema_editor):
    Role = apps.get_model('roles', 'Role')
    Role.objects.filter(slug__in=GRANTED_SLUGS).update(can_manage_market_data=True)


def revoke_permission(apps, schema_editor):
    Role = apps.get_model('roles', 'Role')
    Role.objects.filter(slug__in=GRANTED_SLUGS).update(can_manage_market_data=False)


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0005_role_can_manage_market_data'),
    ]

    operations = [
        migrations.RunPython(grant_permission, revoke_permission),
    ]
