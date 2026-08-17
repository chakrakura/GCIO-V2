from django.conf import settings
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


def _get_filter_list(request, param_name):
    raw_list = request.GET.getlist(param_name)
    cleaned = []
    for item in raw_list:
        for sub in str(item).split(','):
            val = sub.strip()
            if val and val != '__none__' and val not in cleaned:
                cleaned.append(val)
    return cleaned


@permission_required('can_manage_content')
def report_list(request):
    reports = _scoped_reports(request.user).select_related('author', 'publication_type')
    scoped_orgs = _scoped_organizations(request.user)

    query = request.GET.get('q', '').strip()
    if query:
        reports = reports.filter(Q(title__icontains=query) | Q(description__icontains=query))

    status_list = _get_filter_list(request, 'status')
    if status_list:
        reports = reports.filter(status__in=status_list)

    author_ids = _get_filter_list(request, 'author')
    if author_ids:
        reports = reports.filter(author_id__in=author_ids)

    asset_class_ids = _get_filter_list(request, 'asset_class')
    if asset_class_ids:
        reports = reports.filter(asset_classes__id__in=asset_class_ids)

    country_ids = _get_filter_list(request, 'country')
    if country_ids:
        reports = reports.filter(countries_regions__id__in=country_ids)

    publication_type_ids = _get_filter_list(request, 'publication_type')
    if publication_type_ids:
        reports = reports.filter(publication_type_id__in=publication_type_ids)

    tag_ids = _get_filter_list(request, 'tag')
    if tag_ids:
        reports = reports.filter(tags__id__in=tag_ids)

    org_ids = _get_filter_list(request, 'org')
    if org_ids:
        reports = reports.filter(visible_organizations__id__in=org_ids)

    if asset_class_ids or country_ids or tag_ids or org_ids:
        reports = reports.distinct()

    total_count = reports.count()
    page_obj, base_qs = paginate(request, reports)

    authors = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    asset_classes = AssetClass.objects.filter(is_active=True)
    countries_regions = CountryRegion.objects.filter(is_active=True)
    publication_types = PublicationType.objects.filter(is_active=True)
    tags = ReportTag.objects.filter(is_active=True)
    organizations = scoped_orgs

    status_summary = ", ".join([label for val, label in Report.STATUS_CHOICES if val in status_list])
    author_summary = ", ".join([a.get_full_name() or a.username for a in authors if str(a.id) in author_ids])
    asset_class_summary = ", ".join([ac.name for ac in asset_classes if str(ac.id) in asset_class_ids])
    country_summary = ", ".join([c.name for c in countries_regions if str(c.id) in country_ids])
    publication_type_summary = ", ".join([pt.name for pt in publication_types if str(pt.id) in publication_type_ids])
    tag_summary = ", ".join([t.name for t in tags if str(t.id) in tag_ids])
    org_summary = ", ".join([o.name for o in organizations if str(o.id) in org_ids])

    return render(request, 'reports/report_list.html', {
        'active_nav': 'reports',
        'reports': page_obj.object_list,
        'page_obj': page_obj,
        'base_qs': base_qs,
        'query': query,
        'status_list': status_list,
        'status': status_list[0] if status_list else '',
        'status_summary': status_summary,
        'status_choices': Report.STATUS_CHOICES,
        'total_count': total_count,
        'author_ids': author_ids,
        'author_id': author_ids[0] if author_ids else '',
        'author_summary': author_summary,
        'asset_class_ids': asset_class_ids,
        'asset_class_id': asset_class_ids[0] if asset_class_ids else '',
        'asset_class_summary': asset_class_summary,
        'country_ids': country_ids,
        'country_id': country_ids[0] if country_ids else '',
        'country_summary': country_summary,
        'publication_type_ids': publication_type_ids,
        'publication_type_id': publication_type_ids[0] if publication_type_ids else '',
        'publication_type_summary': publication_type_summary,
        'tag_ids': tag_ids,
        'tag_id': tag_ids[0] if tag_ids else '',
        'tag_summary': tag_summary,
        'org_ids': org_ids,
        'org_id': org_ids[0] if org_ids else '',
        'org_summary': org_summary,
        'authors': authors,
        'asset_classes': asset_classes,
        'countries_regions': countries_regions,
        'publication_types': publication_types,
        'tags': tags,
        'organizations': organizations,
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


import os
import zipfile
import pypdf


def _detect_file_page_count(file_obj):
    if not file_obj:
        return None
    name = getattr(file_obj, 'name', '') or str(file_obj)
    name = name.lower()
    try:
        if name.endswith('.pdf'):
            if hasattr(file_obj, 'path') and os.path.exists(file_obj.path):
                return len(pypdf.PdfReader(file_obj.path).pages)
            elif hasattr(file_obj, 'file'):
                file_obj.seek(0)
                return len(pypdf.PdfReader(file_obj).pages)
        elif name.endswith('.pptx') or name.endswith('.ppt'):
            target = file_obj.path if hasattr(file_obj, 'path') and os.path.exists(file_obj.path) else file_obj
            with zipfile.ZipFile(target) as z:
                slides = [f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
                if slides:
                    return len(slides)
    except Exception:
        pass
    return None


@permission_required('can_manage_content')
def report_add(request):
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            report = form.save(commit=False)
            if not report.author_id:
                report.author = request.user
            if report.status == Report.STATUS_PUBLISHED and not report.published_at:
                report.published_at = timezone.now()
            if report.file_upload:
                detected = _detect_file_page_count(report.file_upload)
                if detected:
                    report.page_count = detected
            report.save()
            form.save_m2m()
            log_activity(request, 'created report', report.title)
            messages.success(request, f'"{report.title}" was created.')
            return redirect('report_list')
    else:
        form = ReportForm(initial={'status': Report.STATUS_DRAFT}, user=request.user)

    context = {
        'active_nav': 'reports',
        'form': form,
        'is_edit': False,
        'providers': provider_status(),
        'selected_author_id': None,
    }
    context.update(_pill_context(None, request.user))
    return render(request, 'reports/report_form.html', context)


from modules.client_portal.views import _pptx_preview_pdf_path


def _get_preview_pdf_url(report):
    if not report or not report.file_upload:
        return None
    file_name = report.file_upload.name.lower()
    if file_name.endswith('.pdf'):
        return report.file_upload.url
    elif file_name.endswith('.pptx') or file_name.endswith('.ppt'):
        pdf_path = _pptx_preview_pdf_path(report)
        if pdf_path:
            return f'{settings.MEDIA_URL}reports/converted/{pdf_path.name}'
    return None


@permission_required('can_manage_content')
def report_edit(request, report_id):
    report = get_object_or_404(_scoped_reports(request.user), pk=report_id)

    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, instance=report, user=request.user)
        if form.is_valid():
            report = form.save(commit=False)
            if report.status == Report.STATUS_PUBLISHED and not report.published_at:
                report.published_at = timezone.now()
            if report.file_upload:
                detected = _detect_file_page_count(report.file_upload)
                if detected:
                    report.page_count = detected
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
        'preview_pdf_url': _get_preview_pdf_url(report),
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
