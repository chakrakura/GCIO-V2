from django.db import models
from django.utils.text import slugify


class Organization(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    logo = models.ImageField(upload_to='organizations/logos/', blank=True, null=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    country = models.ForeignKey(
        'taxonomy.CountryRegion', on_delete=models.SET_NULL, blank=True, null=True, related_name='organizations',
    )
    is_active = models.BooleanField(default=True)
    show_gcio_articles = models.BooleanField(
        default=True,
        help_text='Show GCIO articles published to all users. When off, members only see articles assigned to this organisation.',
    )
    custom_domain_enabled = models.BooleanField(
        default=False,
        help_text='Serve the portal on this organisation\'s own domain. Placeholder: not wired up yet.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organizations'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
