from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from gcio.pagination import paginate
from modules.roles.decorators import permission_required
from modules.users.activity import log_activity

from .models import AssetClass, CountryRegion, PublicationType, ReportTag

from modules.users.models import Profile

TAB_CONFIG = {
    'authors': {
        'label': 'Authors',
        'singular': 'author',
        'icon': 'person',
        'model': None,
        'report_param': 'author',
    },
    'asset-classes': {
        'label': 'Asset classes',
        'singular': 'asset class',
        'icon': 'layers',
        'model': AssetClass,
        'report_param': 'asset_class',
        'has_show_on_home': True,
    },
    'countries-regions': {
        'label': 'Countries & regions',
        'singular': 'country or region',
        'icon': 'globe',
        'model': CountryRegion,
        'report_param': 'country',
    },
    'publication-types': {
        'label': 'Publication types',
        'singular': 'publication type',
        'icon': 'book',
        'model': PublicationType,
        'report_param': 'publication_type',
        'has_show_on_home': True,
        'has_series_fields': True,
    },
    'report-tags': {
        'label': 'Report tags',
        'singular': 'report tag',
        'icon': 'tag',
        'model': ReportTag,
        'report_param': 'tag',
    },
}


def _authors_queryset():
    return (
        User.objects.filter(profile__role__is_internal=True, profile__is_author=True)
        .select_related('profile', 'profile__role')
        .annotate(report_count=Count('reports', distinct=True))
        .order_by('first_name', 'last_name')
    )


def _tab_counts():
    counts = {'authors': _authors_queryset().count()}
    for key, cfg in TAB_CONFIG.items():
        if cfg['model'] is not None:
            counts[key] = cfg['model'].objects.count()
    return counts


@permission_required('can_manage_taxonomy')
def taxonomy_view(request, tab='authors'):
    if tab not in TAB_CONFIG:
        tab = 'authors'

    counts = _tab_counts()
    tabs = [
        {'key': key, 'label': cfg['label'], 'icon': cfg['icon'], 'count': counts.get(key, 0)}
        for key, cfg in TAB_CONFIG.items()
    ]

    is_authors = tab == 'authors'
    query = request.GET.get('q', '').strip()
    non_client_users = []

    if is_authors:
        items = _authors_queryset()
        if query:
            items = items.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
            )
        non_client_users = (
            User.objects.filter(profile__role__is_internal=True, profile__is_author=False)
            .select_related('profile', 'profile__role')
            .order_by('first_name', 'last_name')
        )
    else:
        items = TAB_CONFIG[tab]['model'].objects.annotate(report_count=Count('reports', distinct=True))
        if query:
            items = items.filter(name__icontains=query)

    page_obj, base_qs = paginate(request, items)

    return render(request, 'taxonomy/taxonomy.html', {
        'active_nav': 'taxonomy',
        'tabs': tabs,
        'active_tab': tab,
        'active_label': TAB_CONFIG[tab]['label'],
        'active_singular': TAB_CONFIG[tab]['singular'],
        'active_report_param': TAB_CONFIG[tab]['report_param'],
        'has_show_on_home': TAB_CONFIG[tab].get('has_show_on_home', False),
        'has_series_fields': TAB_CONFIG[tab].get('has_series_fields', False),
        'is_authors': is_authors,
        'items': page_obj.object_list,
        'page_obj': page_obj,
        'base_qs': base_qs,
        'query': query,
        'non_client_users': non_client_users,
    })


@permission_required('can_manage_taxonomy')
def taxonomy_add(request, tab):
    if tab == 'authors':
        if request.method == 'POST':
            user_ids = request.POST.getlist('author_user_ids')
            if user_ids:
                updated = Profile.objects.filter(
                    user_id__in=user_ids, role__is_internal=True
                ).update(is_author=True)
                messages.success(request, f'Successfully added {updated} author(s).')
                log_activity(request, 'added authors', f'{updated} user(s)')
            else:
                messages.error(request, 'Please select at least one user to add as an author.')
        return redirect('taxonomy_tab', tab='authors')

    cfg = TAB_CONFIG.get(tab)
    if not cfg or cfg['model'] is None:
        return redirect('taxonomy_tab', tab='authors')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_active = bool(request.POST.get('is_active'))
        if name:
            extra = {}
            if cfg.get('has_show_on_home'):
                extra['show_on_home'] = bool(request.POST.get('show_on_home'))
            if cfg.get('has_series_fields'):
                extra['series_name'] = request.POST.get('series_name', '').strip()
                extra['cadence_label'] = request.POST.get('cadence_label', '').strip()
                extra['description'] = request.POST.get('description', '').strip()
            try:
                cfg['model'].objects.create(name=name, is_active=is_active, **extra)
                log_activity(request, f'added {cfg["singular"]}', name)
            except IntegrityError:
                messages.error(request, f'"{name}" already exists in {cfg["label"]}.')
    return redirect('taxonomy_tab', tab=tab)


@permission_required('can_manage_taxonomy')
def taxonomy_edit(request, tab, term_id):
    cfg = TAB_CONFIG.get(tab)
    if not cfg or cfg['model'] is None:
        return redirect('taxonomy_tab', tab='authors')

    term = get_object_or_404(cfg['model'], pk=term_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            term.name = name
            term.is_active = bool(request.POST.get('is_active'))
            if cfg.get('has_show_on_home'):
                term.show_on_home = bool(request.POST.get('show_on_home'))
            if cfg.get('has_series_fields'):
                term.series_name = request.POST.get('series_name', '').strip()
                term.cadence_label = request.POST.get('cadence_label', '').strip()
                term.description = request.POST.get('description', '').strip()
            try:
                term.save()
                log_activity(request, f'updated {cfg["singular"]}', name)
            except IntegrityError:
                messages.error(request, f'"{name}" already exists in {cfg["label"]}.')
    return redirect('taxonomy_tab', tab=tab)


@permission_required('can_manage_taxonomy')
def taxonomy_delete(request, tab, term_id):
    if tab == 'authors' and request.method == 'POST':
        user = get_object_or_404(User, pk=term_id)
        if hasattr(user, 'profile'):
            user.profile.is_author = False
            user.profile.save()
            log_activity(request, 'removed author', user.get_full_name() or user.username)
            messages.success(request, f'Removed author {user.get_full_name() or user.username}.')
        return redirect('taxonomy_tab', tab='authors')

    cfg = TAB_CONFIG.get(tab)
    if cfg and cfg['model'] is not None and request.method == 'POST':
        term = get_object_or_404(cfg['model'], pk=term_id)
        name = term.name
        term.delete()
        log_activity(request, f'deleted {cfg["singular"]}', name)
    return redirect('taxonomy_tab', tab=tab)
