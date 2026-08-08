from modules.taxonomy.models import AssetClass, PublicationType


def portal_sidebar(request):
    """Sidebar taxonomy/archive data for every client_portal page. Scoped to /portal/ to
    avoid running these queries on every admin-console request too."""
    if not request.path.startswith('/portal/') or not request.user.is_authenticated:
        return {}

    from django.utils import timezone

    from .views import CLIENT_VISIBILITY_WINDOW, _client_reports

    return {
        'asset_classes': AssetClass.objects.filter(is_active=True),
        # Special Report is browsed via its own "Exclusive Reports" sidebar entry, not
        # listed again under the Publications accordion.
        'publication_types': PublicationType.objects.filter(is_active=True).exclude(slug='special-report'),
        # Archive only holds reports older than the 1-year client-visibility window, so its
        # sidebar badge should match that, not the full report count.
        'archive_count': _client_reports(request.user).filter(
            published_at__isnull=False, published_at__lt=timezone.now() - CLIENT_VISIBILITY_WINDOW
        ).count(),
    }
