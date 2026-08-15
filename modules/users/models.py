from django.conf import settings
from django.db import models

from modules.organizations.models import Organization
from modules.roles.models import Role


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='users/photos/', blank=True, null=True)
    title = models.CharField(max_length=150, blank=True, help_text="Byline title shown on authored reports, e.g. \"Head of Research\".")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True, related_name='profiles')
    organizations = models.ManyToManyField(Organization, blank=True, related_name='members')
    is_author = models.BooleanField(default=True, help_text="Whether this user is featured in the Taxonomy authors list.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.get_username()} ({self.role.name if self.role else "No role"})'

    @property
    def is_internal(self):
        return bool(self.role and self.role.is_internal)


class ActivityLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs'
    )
    action = models.CharField(max_length=255)
    target = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        who = self.actor.get_username() if self.actor else 'System'
        return f'{who}: {self.action} {self.target}'.strip()
