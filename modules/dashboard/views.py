from django.contrib.auth.models import User
from django.shortcuts import render
from django.utils import timezone

from modules.organizations.models import Organization
from modules.reports.models import Report
from modules.roles.decorators import permission_required
from modules.users.models import ActivityLog


@permission_required('is_admin_role')
def dashboard_view(request):
    now = timezone.localtime()
    users = User.objects.select_related('profile', 'profile__role').prefetch_related('profile__organizations')
    reports = Report.objects.all()

    stats = {
        'published_reports': reports.filter(status=Report.STATUS_PUBLISHED).count(),
        'published_this_month': reports.filter(
            status=Report.STATUS_PUBLISHED, published_at__year=now.year, published_at__month=now.month
        ).count(),
        'active_users': users.filter(is_active=True).count(),
        'users_this_month': users.filter(date_joined__year=now.year, date_joined__month=now.month).count(),
        'total_organizations': Organization.objects.count(),
        'active_organizations': Organization.objects.filter(is_active=True).count(),
        'draft_reports': reports.filter(status=Report.STATUS_DRAFT).count(),
    }

    recent_activity = ActivityLog.objects.select_related('actor').all()[:8]
    draft_reports = reports.filter(status=Report.STATUS_DRAFT).order_by('-updated_at')[:3]

    role = request.user.profile.role

    return render(request, 'dashboard/dashboard.html', {
        'active_nav': 'dashboard',
        'stats': stats,
        'recent_activity': recent_activity,
        'draft_reports': draft_reports,
        'role': role,
    })
