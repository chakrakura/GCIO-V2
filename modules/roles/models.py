from django.db import models
from django.utils.text import slugify


class Role(models.Model):
    COLOR_CHOICES = [
        ('blue', 'Blue'),
        ('purple', 'Purple'),
        ('gray', 'Gray'),
        ('green', 'Green'),
        ('amber', 'Amber'),
    ]

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='blue')

    is_system = models.BooleanField(default=False, help_text='Built-in role — cannot be deleted.')
    is_internal = models.BooleanField(
        default=True,
        help_text='Internal GCIO staff role with admin console access, as opposed to a client-facing role.'
    )
    can_manage_users = models.BooleanField(default=False, help_text='Create, edit, and deactivate user accounts.')
    can_manage_roles = models.BooleanField(default=False, help_text='Create and edit roles and their permissions.')
    can_manage_organizations = models.BooleanField(default=False, help_text='Create and edit client organisations.')
    can_manage_content = models.BooleanField(default=False, help_text='Upload and manage articles, PDFs, presentations.')
    can_manage_taxonomy = models.BooleanField(
        default=False, help_text='Manage authors and classification taxonomy (asset classes, countries, publication types, tags).'
    )
    can_view_logs = models.BooleanField(default=False, help_text='View the admin actions log.')
    can_view_all_organizations = models.BooleanField(
        default=False,
        help_text='See content for every organisation, not just the ones assigned to this user.'
    )
    can_manage_market_data = models.BooleanField(
        default=False, help_text='Manage market data instruments and refresh prices from Yahoo Finance.'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'roles'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def user_count(self):
        return self.profiles.count()

    @property
    def is_admin_role(self):
        return bool(self.can_manage_users or self.can_manage_organizations or self.can_manage_roles)
