from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from modules.roles.models import Role

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        default_slug = 'super-admin' if instance.is_superuser else 'client-user'
        default_role = Role.objects.filter(slug=default_slug).first()
        Profile.objects.get_or_create(user=instance, defaults={'role': default_role})


@receiver(post_save, sender=Profile)
def sync_admin_access(sender, instance, **kwargs):
    """Keep Django admin (/admin/) access in sync with the role's permissions:
    internal roles can log in to /admin/; only roles that can manage roles
    (Super Admin) get unrestricted superuser access there.
    """
    role = instance.role
    is_staff = bool(role and role.is_internal)
    is_superuser = bool(role and role.can_manage_roles)
    user = instance.user
    if user.is_staff != is_staff or user.is_superuser != is_superuser:
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save(update_fields=['is_staff', 'is_superuser'])
