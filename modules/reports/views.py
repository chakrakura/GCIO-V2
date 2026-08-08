from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from gcio.pagination import paginate
from modules.organizations.models import Organization
from modules.roles.decorators import permission_required
from modules.taxonomy.models import AssetClass, CountryRegion, PublicationType, ReportTag
from modules.users.activity import log_activity

from .ai import GeminiConfigError, GeminiRequestError, generate_draft, provider_status
from .forms import ReportForm
from .models import Report


def _can_view_all_orgs(user):
    role = getattr(user.profile, 'role', None)
    return user.is_superuser or bool(role and role.can_view_all_organizations)


def _scoped_organizations(user):
    if _can_view_all_orgs(user):
        return Organization.objects.filter(is_active=True)
    return user.profile.organizations.filter(is_active=True)


def _scoped_reports(user):
    reports = Report.objects.all()
    if _can_view_all_orgs(user):
        return reports
    scoped_orgs = _scoped_organizations(user)
    return reports.filter(
        Q(access_level=Report.ACCESS_ALL) | Q(author=user) | Q(visible_organizations__in=scoped_orgs)
    ).distinct()


@permission_required('can_manage_content')
def report_list(request):
    reports = _scoped_reports(request.user).select_related('author', 'publication_type')
    scoped_orgs = _scoped_organizations(request.user)

    query = request.GET.get('q', '').strip()
    if query:
        reports = reports.filter(Q(title__icontains=query) | Q(description__icontains=query))

    status = request.GET.get('status', '')
    if status:
        reports = reports.filter(status=status)

    filter_author = None
    author_id = request.GET.get('author', '').strip()
    if author_id:
        reports = reports.filter(author_id=author_id)
        filter_author = User.objects.filter(pk=author_id).first()

    filter_asset_class = None
    asset_class_id = request.GET.get('asset_class', '').strip()
    if asset_class_id:
        reports = reports.filter(asset_classes__id=asset_class_id)
        filter_asset_class = AssetClass.objects.filter(pk=asset_class_id).first()

    filter_country = None
    country_id = request.GET.get('country', '').strip()
    if country_id:
        reports = reports.filter(countries_regions__id=country_id)
        filter_country = CountryRegion.objects.filter(pk=country_id).first()

    filter_publication_type = None
    publication_type_id = request.GET.get('publication_type', '').strip()
    if publication_type_id:
        reports = reports.filter(publication_type_id=publication_type_id)
        filter_publication_type = PublicationType.objects.filter(pk=publication_type_id).first()

    filter_tag = None
    tag_id = request.GET.get('tag', '').strip()
    if tag_id:
        reports = reports.filter(tags__id=tag_id)
        filter_tag = ReportTag.objects.filter(pk=tag_id).first()

    filter_org = None
    org_id = request.GET.get('org', '').strip()
    if org_id:
        reports = reports.filter(visible_organizations__id=org_id)
        filter_org = scoped_orgs.filter(pk=org_id).first()

    if asset_class_id or country_id or tag_id or org_id:
        reports = reports.distinct()

    filter_label = None
    if filter_author:
        filter_label = f'Author: {filter_author.get_full_name() or filter_author.username}'
    elif filter_asset_class:
        filter_label = f'Asset class: {filter_asset_class.name}'
    elif filter_country:
        filter_label = f'Country/region: {filter_country.name}'
    elif filter_publication_type:
        filter_label = f'Publication type: {filter_publication_type.name}'
    elif filter_tag:
        filter_label = f'Tag: {filter_tag.name}'
    elif filter_org:
        filter_label = f'Organisation: {filter_org.name}'

    total_count = reports.count()
    page_obj, base_qs = paginate(request, reports)

    return render(request, 'reports/report_list.html', {
        'active_nav': 'reports',
        'reports': page_obj.object_list,
        'page_obj': page_obj,
        'base_qs': base_qs,
        'query': query,
        'status': status,
        'status_choices': Report.STATUS_CHOICES,
        'total_count': total_count,
        'filter_label': filter_label,
        'author_id': author_id,
        'asset_class_id': asset_class_id,
        'country_id': country_id,
        'publication_type_id': publication_type_id,
        'tag_id': tag_id,
        'org_id': org_id,
        'authors': User.objects.filter(profile__role__is_internal=True).order_by('first_name', 'last_name'),
        'asset_classes': AssetClass.objects.filter(is_active=True),
        'countries_regions': CountryRegion.objects.filter(is_active=True),
        'publication_types': PublicationType.objects.filter(is_active=True),
        'tags': ReportTag.objects.filter(is_active=True),
        'organizations': scoped_orgs,
    })


def _pill_context(report, user):
    selected_asset_classes = set(report.asset_classes.values_list('id', flat=True)) if report else set()
    selected_countries_regions = set(report.countries_regions.values_list('id', flat=True)) if report else set()
    selected_tags = set(report.tags.values_list('id', flat=True)) if report else set()
    selected_orgs = set(report.visible_organizations.values_list('id', flat=True)) if report else set()

    org_options = _scoped_organizations(user)
    if selected_orgs:
        org_options = Organization.objects.filter(Q(pk__in=org_options) | Q(pk__in=selected_orgs))

    return {
        'asset_class_options': AssetClass.objects.filter(is_active=True),
        'selected_asset_classes': selected_asset_classes,
        'country_region_options': CountryRegion.objects.filter(is_active=True),
        'selected_countries_regions': selected_countries_regions,
        'tag_options': ReportTag.objects.filter(is_active=True),
        'selected_tags': selected_tags,
        'org_options': org_options,
        'selected_orgs': selected_orgs,
        'author_options': User.objects.filter(profile__role__is_internal=True).order_by('first_name', 'last_name'),
    }


@permission_required('can_manage_content')
def report_add(request):
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            report = form.save(commit=False)
            if not report.author_id:
                report.author = request.user
            if report.status == Report.STATUS_PUBLISHED:
                report.published_at = timezone.now()
            report.save()
            form.save_m2m()
            log_activity(request, 'created report', report.title)
            messages.success(request, f'"{report.title}" was created.')
            return redirect('report_list')
    else:
        form = ReportForm(initial={'status': Report.STATUS_DRAFT, 'author': request.user}, user=request.user)

    context = {
        'active_nav': 'reports',
        'form': form,
        'is_edit': False,
        'providers': provider_status(),
        'selected_author_id': request.user.id,
    }
    context.update(_pill_context(None, request.user))
    return render(request, 'reports/report_form.html', context)


@permission_required('can_manage_content')
def report_edit(request, report_id):
    report = get_object_or_404(_scoped_reports(request.user), pk=report_id)

    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, instance=report, user=request.user)
        if form.is_valid():
            was_published = report.published_at is not None
            report = form.save(commit=False)
            if report.status == Report.STATUS_PUBLISHED and not was_published:
                report.published_at = timezone.now()
            report.save()
            form.save_m2m()
            log_activity(request, 'updated report', report.title)
            messages.success(request, f'"{report.title}" was updated.')
            return redirect('report_list')
    else:
        form = ReportForm(instance=report, user=request.user)

    context = {
        'active_nav': 'reports',
        'form': form,
        'is_edit': True,
        'report': report,
        'providers': provider_status(),
        'selected_author_id': report.author_id,
    }
    context.update(_pill_context(report, request.user))
    return render(request, 'reports/report_form.html', context)


@permission_required('can_manage_content')
def report_delete(request, report_id):
    report = get_object_or_404(_scoped_reports(request.user), pk=report_id)
    if request.method == 'POST':
        title = report.title
        report.delete()
        log_activity(request, 'deleted report', title)
        messages.success(request, f'"{title}" was deleted.')
    return redirect('report_list')


@permission_required('can_manage_content')
@require_POST
def generate_ai_draft(request):
    prompt = request.POST.get('prompt', '').strip()
    if not prompt:
        return JsonResponse({'error': 'Describe what you want to generate first.'}, status=400)

    try:
        title, body_html = generate_draft(prompt)
    except GeminiConfigError as exc:
        return JsonResponse({'error': str(exc)}, status=503)
    except GeminiRequestError as exc:
        return JsonResponse({'error': f'Gemini request failed: {exc}'}, status=502)

    return JsonResponse({'title': title, 'body_html': body_html})
