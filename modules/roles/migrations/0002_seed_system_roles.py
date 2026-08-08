from django.db import migrations


SYSTEM_ROLES = [
    {
        'name': 'Super Admin',
        'slug': 'super-admin',
        'description': 'Full control, including managing other admins and roles.',
        'color': 'blue',
        'is_system': True,
        'is_internal': True,
        'can_manage_users': True,
        'can_manage_roles': True,
        'can_manage_organizations': True,
        'can_manage_content': True,
        'can_view_all_organizations': True,
    },
    {
        'name': 'Administrator',
        'slug': 'administrator',
        'description': 'Manages users, organisations, and content. Cannot change roles or permissions.',
        'color': 'blue',
        'is_system': True,
        'is_internal': True,
        'can_manage_users': True,
        'can_manage_roles': False,
        'can_manage_organizations': True,
        'can_manage_content': True,
        'can_view_all_organizations': True,
    },
    {
        'name': 'Content Editor',
        'slug': 'content-editor',
        'description': 'Uploads and manages articles, PDFs, and presentations, and assigns them to organisations.',
        'color': 'purple',
        'is_system': True,
        'is_internal': True,
        'can_manage_users': False,
        'can_manage_roles': False,
        'can_manage_organizations': False,
        'can_manage_content': True,
        'can_view_all_organizations': True,
    },
    {
        'name': 'Client User',
        'slug': 'client-user',
        'description': 'Read-only access to content assigned to their organisation.',
        'color': 'gray',
        'is_system': True,
        'is_internal': False,
        'can_manage_users': False,
        'can_manage_roles': False,
        'can_manage_organizations': False,
        'can_manage_content': False,
        'can_view_all_organizations': False,
    },
]


def seed_roles(apps, schema_editor):
    Role = apps.get_model('roles', 'Role')
    for data in SYSTEM_ROLES:
        Role.objects.get_or_create(slug=data['slug'], defaults=data)


def remove_roles(apps, schema_editor):
    Role = apps.get_model('roles', 'Role')
    Role.objects.filter(slug__in=[r['slug'] for r in SYSTEM_ROLES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_roles, remove_roles),
    ]
