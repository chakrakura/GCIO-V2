import subprocess
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from modules.market_data.models import MarketInstrument
from modules.reports.models import Report, SavedReport
from modules.taxonomy.models import AssetClass, CountryRegion, PublicationType

DATE_RANGE_OPTIONS = [
    ('7d', 'Last 7 days'),
    ('30d', 'Last 30 days'),
    ('90d', 'Last 3 months'),
    ('365d', 'Last 12 months'),
    ('all', 'All time'),
]
DATE_RANGE_DAYS = {'7d': 7, '30d': 30, '90d': 90, '365d': 365}

NEW_BADGE_WINDOW = timedelta(days=3)

CONVERTED_PREVIEWS_DIR = Path(settings.MEDIA_ROOT) / 'reports' / 'converted'

# Symbol used for the hero chart's live value/change header — the trend line
# itself is still illustrative (see HERO_CHART_SERIES) but the headline number
# is real, pulled from the market_data app whenever that instrument has data.
HERO_CHART_SYMBOL = '^TYX'

# Small fixed palette for the colored dot next to a report's publication type
# on Featured Research cards — cosmetic only, not stored on PublicationType.
PUBLICATION_TYPE_DOT_COLORS = {
    'special-report': 'bg-red-500',
    'weekly-insight': 'bg-blue-500',
    'monthly-digest': 'bg-purple-500',
    'daily-note': 'bg-green-500',
    'quarterly-review': 'bg-amber-500',
    'annual-outlook': 'bg-gray-400',
}
DEFAULT_DOT_COLOR = 'bg-blue-500'

# The hero chart's trend LINE is still illustrative — this app has no historical
# market-data feed, only latest-price snapshots (see modules.market_data), so
# this fixed shape stands in for a real time series. The headline value/change
# shown above the chart, however, is real — pulled live from HERO_CHART_SYMBOL,
# with these as a fallback only if that instrument has no data yet.
HERO_CHART_LABEL = 'US 30Y Treasury Yield'
HERO_CHART_VALUE_FALLBACK = '5.06%'
HERO_CHART_CHANGE_FALLBACK = '+60bp'
HERO_CHART_CAPTION = 'Through 5.00% on a sustained basis · illustrative trend'
HERO_CHART_SERIES = [3.78, 3.85, 3.92, 4.05, 4.18, 4.12, 4.30, 4.42, 4.55, 4.68, 4.80, 4.92, 4.97, 5.06]
HERO_CHART_THRESHOLD = 5.0
HERO_CHART_AXIS_RANGE = (3.7, 5.15)
HERO_CHART_GRIDLINES = (5.0, 4.5, 4.0)

WORDS_PER_MINUTE = 200
MINUTES_PER_SLIDE_OR_PAGE = 2


def _build_hero_chart():
    """Precompute SVG coordinates for the hero chart — plain inline SVG, no JS charting lib."""
    live_instrument = MarketInstrument.objects.filter(symbol=HERO_CHART_SYMBOL, last_price__isnull=False).first()
    value = live_instrument.formatted_value if live_instrument else HERO_CHART_VALUE_FALLBACK
    change = live_instrument.formatted_change if live_instrument else HERO_CHART_CHANGE_FALLBACK

    width, height = 400, 150
    pad_left, pad_right, pad_top, pad_bottom = 34, 10, 14, 10
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    lo, hi = HERO_CHART_AXIS_RANGE

    def y_for(value):
        return pad_top + plot_h * (1 - (value - lo) / (hi - lo))

    def x_for(index):
        return pad_left + plot_w * index / (len(HERO_CHART_SERIES) - 1)

    points = ' '.join(f'{x_for(i):.1f},{y_for(v):.1f}' for i, v in enumerate(HERO_CHART_SERIES))
    shade_start_index = len(HERO_CHART_SERIES) - 4
    last_index = len(HERO_CHART_SERIES) - 1
    shade_x = x_for(shade_start_index)

    return {
        'width': width,
        'height': height,
        'pad_left': pad_left,
        'plot_top': pad_top,
        'plot_height': plot_h,
        'points': points,
        'gridlines': [(f'{v:.1f}', round(y_for(v), 1)) for v in HERO_CHART_GRIDLINES],
        'threshold_y': round(y_for(HERO_CHART_THRESHOLD), 1),
        'shade_x': round(shade_x, 1),
        'shade_width': round(width - pad_right - shade_x, 1),
        'last_x': round(x_for(last_index), 1),
        'last_y': round(y_for(HERO_CHART_SERIES[last_index]), 1),
        'label': HERO_CHART_LABEL,
        'value': value,
        'change': change,
        'caption': HERO_CHART_CAPTION,
    }


def _estimated_reading_minutes(report):
    """Rough reading-time estimate — word count for text, page count otherwise."""
    if report.content_type == Report.CONTENT_TEXT:
        word_count = len((report.body or '').split())
        return max(1, round(word_count / WORDS_PER_MINUTE))
    return max(1, report.page_count * MINUTES_PER_SLIDE_OR_PAGE)


def _dot_color(publication_type):
    slug = publication_type.slug if publication_type else None
    return PUBLICATION_TYPE_DOT_COLORS.get(slug, DEFAULT_DOT_COLOR)


def _client_reports(user):
    """Published reports visible to this user's organisation(s)."""
    org_ids = list(user.profile.organizations.values_list('id', flat=True))
    return Report.objects.filter(status=Report.STATUS_PUBLISHED).filter(
        Q(access_level=Report.ACCESS_ALL) | Q(visible_organizations__id__in=org_ids)
    ).distinct().select_related('author', 'publication_type').order_by('-published_at')


CLIENT_VISIBILITY_WINDOW = timedelta(days=365)


def _client_reports_current(user):
    """Reports shown on every client-facing listing (Home, Research, Saved, Publications,
    series pages) — capped to the last 12 months. Older reports are only browsable via the
    Archive, which calls _client_reports() directly to see the full historical catalogue."""
    return _client_reports(user).filter(published_at__gte=timezone.now() - CLIENT_VISIBILITY_WINDOW)


def _is_client_role(user):
    role = getattr(user.profile, 'role', None)
    return bool(role and not role.is_internal)


def _saved_report_ids(user):
    return set(SavedReport.objects.filter(user=user).values_list('report_id', flat=True))


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _pptx_preview_pdf_path(report):
    """Convert a .pptx/.ppt upload to PDF via headless LibreOffice, caching the result.

    LibreOffice's own rendering engine handles embedded EMF/WMF images (common for
    charts pasted from Excel) that no browser can decode, so this gives a faithful
    preview instead of relying on client-side pptx parsing for visual fidelity.
    """
    src_path = Path(report.file_upload.path)
    out_name = f'{report.id}_{src_path.stem}.pdf'
    out_path = CONVERTED_PREVIEWS_DIR / out_name

    if out_path.exists() and out_path.stat().st_mtime >= src_path.stat().st_mtime:
        return out_path

    CONVERTED_PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', str(CONVERTED_PREVIEWS_DIR), str(src_path)],
            check=True, timeout=120, capture_output=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None

    produced = CONVERTED_PREVIEWS_DIR / f'{src_path.stem}.pdf'
    if not produced.exists():
        return None
    if produced != out_path:
        produced.replace(out_path)
    return out_path


def _pdf_page_count(pdf_path):
    try:
        return len(PdfReader(str(pdf_path)).pages)
    except (PdfReadError, OSError, ValueError):
        return None


@login_required
def client_home(request):
    if not _is_client_role(request.user):
        return redirect('dashboard')

    # Featured Research is curated by staff via the "Feature on client home page"
    # checkbox on the report form — shows the 3 most recent reports marked featured.
    reports = list(_client_reports_current(request.user).filter(is_featured=True)[:3])
    featured = reports[0] if reports else None
    other_reports = reports[1:3]
    featured_ids = [r.id for r in reports[:3]]

    if featured:
        featured.reading_minutes = _estimated_reading_minutes(featured)
        featured.dot_color = _dot_color(featured.publication_type)
    for report in other_reports:
        report.reading_minutes = _estimated_reading_minutes(report)
        report.dot_color = _dot_color(report.publication_type)

    active_instruments = list(MarketInstrument.objects.filter(is_active=True))
    ticker = [i.as_ticker_tuple() for i in active_instruments]
    hero_stats = [i.as_ticker_tuple() for i in active_instruments if i.is_hero_stat]
    hero_chart = _build_hero_chart() if featured else None

    asset_class_id = request.GET.get('asset_class', '').strip()
    latest_qs = _client_reports_current(request.user).exclude(id__in=featured_ids).exclude(
        publication_type__slug='special-report'
    )
    if asset_class_id:
        latest_qs = latest_qs.filter(asset_classes__id=asset_class_id)
    latest_research = list(latest_qs.prefetch_related('asset_classes', 'tags')[:6])
    for report in latest_research:
        report.reading_minutes = _estimated_reading_minutes(report)
        report.dot_color = _dot_color(report.publication_type)

    saved_report_ids = _saved_report_ids(request.user)

    visible_report_ids = list(_client_reports_current(request.user).values_list('id', flat=True))
    asset_classes = list(AssetClass.objects.filter(is_active=True).annotate(
        report_count=Count(
            'reports', filter=Q(reports__id__in=visible_report_ids), distinct=True,
        )
    ))

    if _is_ajax(request):
        return render(request, 'client_portal/partials/latest_research.html', {
            'latest_research': latest_research,
            'asset_class_id': asset_class_id,
            'asset_classes': asset_classes,
            'saved_report_ids': saved_report_ids,
        })

    # "Research by Asset Class" only shows classes staff opted in via show_on_home —
    # the filter tabs above still list every active asset class regardless.
    featured_asset_classes = [ac for ac in asset_classes if ac.show_on_home]
    for ac in featured_asset_classes:
        ac.latest_report = _client_reports_current(request.user).filter(asset_classes=ac).first()

    home_publication_types = list(PublicationType.objects.filter(is_active=True, show_on_home=True).annotate(
        report_count=Count(
            'reports', filter=Q(reports__id__in=visible_report_ids), distinct=True,
        )
    ))
    for pt in home_publication_types:
        pt.latest_report = _client_reports_current(request.user).filter(publication_type=pt).first()

    new_since_login = 0
    previous_login_raw = request.session.get('previous_login')
    if previous_login_raw:
        previous_login = parse_datetime(previous_login_raw)
        if previous_login:
            new_since_login = _client_reports_current(request.user).filter(published_at__gt=previous_login).count()

    hour = timezone.localtime().hour
    if hour < 12:
        greeting = 'morning'
    elif hour < 18:
        greeting = 'afternoon'
    else:
        greeting = 'evening'

    return render(request, 'client_portal/home.html', {
        'active_nav': 'home',
        'featured': featured,
        'other_reports': other_reports,
        'hero_stats': hero_stats,
        'hero_chart': hero_chart,
        'latest_research': latest_research,
        'asset_class_id': asset_class_id,
        'asset_classes': asset_classes,
        'featured_asset_classes': featured_asset_classes,
        'home_publication_types': home_publication_types,
        'new_since_login': new_since_login,
        'greeting': greeting,
        'ticker': ticker,
        'saved_report_ids': saved_report_ids,
    })


SORT_OPTIONS = {
    'newest': '-published_at',
    'oldest': 'published_at',
    'title': 'title',
}
RESEARCH_PAGE_SIZE = 10


def _apply_report_filters(request, reports, default_asset_class_ids=None, default_date_range=None):
    """Shared filter set for the Research, Saved Reports and Archive pages — asset class,
    geography, author, format, publication date and free-text search. Publication type isn't
    part of this set: that dimension is browsed via the dedicated Publications series pages.

    default_asset_class_ids / default_date_range let a specific page (currently just Research)
    pre-select filters on first load, before the user has touched anything. Following the
    "Clear" link (?cleared=1) skips those defaults so it actually clears everything, rather
    than bouncing back to the pre-selected state.
    """
    cleared = request.GET.get('cleared') == '1'

    asset_class_ids = request.GET.getlist('asset_class')
    if not asset_class_ids and not cleared:
        asset_class_ids = [str(i) for i in (default_asset_class_ids or [])]
    if asset_class_ids:
        reports = reports.filter(asset_classes__id__in=asset_class_ids).distinct()

    region_ids = request.GET.getlist('region')
    if region_ids:
        reports = reports.filter(countries_regions__id__in=region_ids).distinct()

    author_ids = request.GET.getlist('author')
    if author_ids:
        reports = reports.filter(author_id__in=author_ids)

    format_values = request.GET.getlist('format')
    if format_values:
        reports = reports.filter(content_type__in=format_values)

    date_range = request.GET.get('date_range', '').strip()
    if not date_range and not cleared:
        date_range = default_date_range or ''
    if date_range in DATE_RANGE_DAYS:
        cutoff = timezone.now() - timedelta(days=DATE_RANGE_DAYS[date_range])
        reports = reports.filter(published_at__gte=cutoff)

    query = request.GET.get('q', '').strip()
    if query:
        reports = reports.filter(Q(title__icontains=query) | Q(description__icontains=query))

    sort = request.GET.get('sort', 'newest')
    reports = reports.order_by(SORT_OPTIONS.get(sort, SORT_OPTIONS['newest'])).prefetch_related(
        'asset_classes', 'countries_regions', 'tags'
    )

    selections = {
        'selected_asset_classes': set(asset_class_ids),
        'selected_regions': set(region_ids),
        'selected_authors': set(author_ids),
        'selected_formats': set(format_values),
        'selected_date_range': date_range,
        'query': query,
        'sort': sort,
    }
    return reports, selections


def _report_filter_facets(visible_report_ids):
    """Filter option lists (with counts) for the shared filters sidebar."""
    User = get_user_model()
    return {
        'asset_class_filters': AssetClass.objects.filter(is_active=True).annotate(
            report_count=Count('reports', filter=Q(reports__id__in=visible_report_ids), distinct=True)
        ),
        'region_filters': CountryRegion.objects.filter(is_active=True).annotate(
            report_count=Count('reports', filter=Q(reports__id__in=visible_report_ids), distinct=True)
        ),
        'author_filters': User.objects.filter(reports__id__in=visible_report_ids).annotate(
            report_count=Count('reports', filter=Q(reports__id__in=visible_report_ids), distinct=True)
        ).distinct().order_by('first_name', 'last_name'),
        'format_filters': [
            {
                'value': value,
                'label': label,
                'count': Report.objects.filter(id__in=visible_report_ids, content_type=value).count(),
            }
            for value, label in Report.CONTENT_TYPE_CHOICES
        ],
        'date_range_options': DATE_RANGE_OPTIONS,
    }


def _paginate_reports(request, reports):
    paginator = Paginator(reports, RESEARCH_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))
    reports = list(page_obj)

    new_cutoff = timezone.now() - NEW_BADGE_WINDOW
    for report in reports:
        report.reading_minutes = _estimated_reading_minutes(report)
        report.dot_color = _dot_color(report.publication_type)
        report.is_new = bool(report.published_at and report.published_at >= new_cutoff)

    return paginator, page_obj, reports


def _render_report_list_page(
    request, template_name, base_reports, active_nav, clear_url,
    default_asset_class_ids=None, default_date_range=None,
):
    visible_report_ids = list(base_reports.values_list('id', flat=True))
    reports, selections = _apply_report_filters(
        request, base_reports,
        default_asset_class_ids=default_asset_class_ids, default_date_range=default_date_range,
    )
    paginator, page_obj, reports = _paginate_reports(request, reports)

    if _is_ajax(request):
        response = render(request, 'client_portal/partials/research_cards_page.html', {
            'reports': reports,
            'saved_report_ids': _saved_report_ids(request.user),
        })
        response['X-Has-Next-Page'] = '1' if page_obj.has_next() else '0'
        response['X-Next-Page'] = page_obj.next_page_number() if page_obj.has_next() else ''
        return response

    querystring_params = request.GET.copy()
    querystring_params.pop('page', None)
    querystring = querystring_params.urlencode()

    range_link_params = request.GET.copy()
    range_link_params.pop('page', None)
    range_link_params.pop('date_range', None)
    range_link_base = range_link_params.urlencode()

    context = {
        'active_nav': active_nav,
        'clear_url': clear_url,
        'reports': reports,
        'report_count': paginator.count,
        'page_obj': page_obj,
        'querystring': querystring,
        'range_link_base': range_link_base,
        'saved_report_ids': _saved_report_ids(request.user),
        'hide_date_range': True,
        **selections,
    }
    context.update(_report_filter_facets(visible_report_ids))
    return render(request, template_name, context)


@login_required
def client_browse(request):
    if not _is_client_role(request.user):
        return redirect('dashboard')

    # Special Report lives under its own "Exclusive Reports" series page, so it's excluded
    # from this general research browse entirely — not just unchecked by default.
    base_reports = _client_reports_current(request.user).exclude(publication_type__slug='special-report')

    return _render_report_list_page(
        request, 'client_portal/browse.html', base_reports, 'research',
        reverse('client_browse') + '?cleared=1',
        default_asset_class_ids=list(AssetClass.objects.filter(is_active=True).values_list('id', flat=True)),
        default_date_range='30d',
    )


@login_required
def client_publications(request):
    if not _is_client_role(request.user):
        return redirect('dashboard')

    # Special Report lives under its own "Exclusive Reports" series page, so it's excluded
    # from this general publications browse entirely — not just unchecked by default.
    all_reports = _client_reports_current(request.user).exclude(publication_type__slug='special-report')
    visible_report_ids = list(all_reports.values_list('id', flat=True))

    cleared = request.GET.get('cleared') == '1'
    default_publication_type_ids = [
        str(pk) for pk in PublicationType.objects.filter(is_active=True)
        .exclude(slug='special-report').values_list('id', flat=True)
    ]
    publication_type_ids = request.GET.getlist('publication_type')
    if not publication_type_ids and not cleared:
        publication_type_ids = default_publication_type_ids

    reports = all_reports
    if publication_type_ids:
        reports = reports.filter(publication_type_id__in=publication_type_ids)

    reports, selections = _apply_report_filters(request, reports, default_date_range='365d')
    paginator, page_obj, reports = _paginate_reports(request, reports)

    if _is_ajax(request):
        response = render(request, 'client_portal/partials/research_cards_page.html', {
            'reports': reports,
            'saved_report_ids': _saved_report_ids(request.user),
        })
        response['X-Has-Next-Page'] = '1' if page_obj.has_next() else '0'
        response['X-Next-Page'] = page_obj.next_page_number() if page_obj.has_next() else ''
        return response

    querystring_params = request.GET.copy()
    querystring_params.pop('page', None)
    querystring = querystring_params.urlencode()

    range_link_params = request.GET.copy()
    range_link_params.pop('page', None)
    range_link_params.pop('date_range', None)
    range_link_base = range_link_params.urlencode()

    publication_type_filters = PublicationType.objects.filter(is_active=True).exclude(
        slug='special-report'
    ).annotate(
        report_count=Count('reports', filter=Q(reports__id__in=visible_report_ids), distinct=True)
    )

    context = {
        'active_nav': 'publications',
        'reports': reports,
        'report_count': paginator.count,
        'page_obj': page_obj,
        'querystring': querystring,
        'range_link_base': range_link_base,
        'publication_type_filters': publication_type_filters,
        'selected_publication_types': set(publication_type_ids),
        'clear_url': reverse('client_publications') + '?cleared=1',
        'saved_report_ids': _saved_report_ids(request.user),
        'hide_date_range': True,
        **selections,
    }
    context.update(_report_filter_facets(visible_report_ids))
    return render(request, 'client_portal/publications.html', context)


@login_required
def client_publication_series(request, slug):
    if not _is_client_role(request.user):
        return redirect('dashboard')

    # Exclusive Reports has its own standalone page — redirect rather than serve the
    # generic series view at this slug too.
    if slug == 'special-report':
        return redirect('client_exclusive_reports')

    publication_type = get_object_or_404(PublicationType, slug=slug, is_active=True)

    # The Publication Type filter defaults to just this series, but checking others broadens
    # the results without leaving the page.
    publication_type_ids = request.GET.getlist('publication_type') or [str(publication_type.id)]
    base_reports = _client_reports_current(request.user).filter(publication_type_id__in=publication_type_ids)
    total_count = base_reports.count()
    visible_report_ids = list(base_reports.values_list('id', flat=True))

    all_current_report_ids = list(_client_reports_current(request.user).values_list('id', flat=True))
    publication_type_filters = PublicationType.objects.filter(is_active=True).annotate(
        report_count=Count('reports', filter=Q(reports__id__in=all_current_report_ids), distinct=True)
    )

    # Same date-range options/default as the Publications hub (/portal/publications/) —
    # kept as page-specific pills here (like the hub's own filter) rather than the shared
    # aside section, but sharing its param name, option set and 12-month default.
    reports_qs, selections = _apply_report_filters(request, base_reports, default_date_range='365d')
    paginator, page_obj, reports = _paginate_reports(request, reports_qs)

    if _is_ajax(request):
        response = render(request, 'client_portal/partials/research_cards_page.html', {
            'reports': reports,
            'saved_report_ids': _saved_report_ids(request.user),
        })
        response['X-Has-Next-Page'] = '1' if page_obj.has_next() else '0'
        response['X-Next-Page'] = page_obj.next_page_number() if page_obj.has_next() else ''
        return response

    querystring_params = request.GET.copy()
    querystring_params.pop('page', None)
    querystring = querystring_params.urlencode()

    range_link_params = request.GET.copy()
    range_link_params.pop('page', None)
    range_link_params.pop('date_range', None)
    range_link_base = range_link_params.urlencode()

    contributors = get_user_model().objects.filter(
        id__in=base_reports.values_list('author_id', flat=True)
    ).order_by('first_name', 'last_name')

    context = {
        'active_nav': 'publications',
        'publication_type': publication_type,
        'dot_color': _dot_color(publication_type),
        'total_count': total_count,
        'report_count': paginator.count,
        'reports': reports,
        'page_obj': page_obj,
        'querystring': querystring,
        'range_link_base': range_link_base,
        'clear_url': reverse('client_publication_series', args=[slug]) + '?cleared=1',
        'contributors': contributors,
        'publication_type_filters': publication_type_filters,
        'selected_publication_types': set(publication_type_ids),
        'saved_report_ids': _saved_report_ids(request.user),
        'hide_date_range': True,
        **selections,
    }
    context.update(_report_filter_facets(visible_report_ids))
    return render(request, 'client_portal/publication_series.html', context)


@login_required
def client_exclusive_reports(request):
    """Exclusive Reports (Special Report issues) — a standalone sidebar destination in its
    own right, not a link into the generic Publications series page."""
    if not _is_client_role(request.user):
        return redirect('dashboard')

    publication_type = get_object_or_404(PublicationType, slug='special-report', is_active=True)
    base_reports = _client_reports_current(request.user).filter(publication_type=publication_type)
    total_count = base_reports.count()
    visible_report_ids = list(base_reports.values_list('id', flat=True))

    reports_qs, selections = _apply_report_filters(request, base_reports, default_date_range='365d')
    paginator, page_obj, reports = _paginate_reports(request, reports_qs)

    if _is_ajax(request):
        response = render(request, 'client_portal/partials/research_cards_page.html', {
            'reports': reports,
            'saved_report_ids': _saved_report_ids(request.user),
        })
        response['X-Has-Next-Page'] = '1' if page_obj.has_next() else '0'
        response['X-Next-Page'] = page_obj.next_page_number() if page_obj.has_next() else ''
        return response

    querystring_params = request.GET.copy()
    querystring_params.pop('page', None)
    querystring = querystring_params.urlencode()

    range_link_params = request.GET.copy()
    range_link_params.pop('page', None)
    range_link_params.pop('date_range', None)
    range_link_base = range_link_params.urlencode()

    contributors = get_user_model().objects.filter(
        id__in=_client_reports_current(request.user).filter(publication_type=publication_type).values_list(
            'author_id', flat=True
        )
    ).order_by('first_name', 'last_name')

    context = {
        'active_nav': 'exclusive',
        'publication_type': publication_type,
        'dot_color': _dot_color(publication_type),
        'total_count': total_count,
        'report_count': paginator.count,
        'reports': reports,
        'page_obj': page_obj,
        'querystring': querystring,
        'range_link_base': range_link_base,
        'clear_url': reverse('client_exclusive_reports') + '?cleared=1',
        'contributors': contributors,
        'saved_report_ids': _saved_report_ids(request.user),
        'hide_date_range': True,
        **selections,
    }
    context.update(_report_filter_facets(visible_report_ids))
    return render(request, 'client_portal/exclusive_reports.html', context)


@login_required
def client_saved_reports(request):
    if not _is_client_role(request.user):
        return redirect('dashboard')

    visible_ids = _client_reports_current(request.user).values_list('id', flat=True)
    saved_ids = SavedReport.objects.filter(user=request.user).values_list('report_id', flat=True)
    all_reports = Report.objects.filter(id__in=saved_ids).filter(id__in=visible_ids).select_related(
        'author', 'publication_type'
    )
    visible_report_ids = list(all_reports.values_list('id', flat=True))

    publication_type_ids = request.GET.getlist('publication_type')
    reports = all_reports
    if publication_type_ids:
        reports = reports.filter(publication_type_id__in=publication_type_ids)

    # Saved Reports gets the full filter set (including Publication Type, unlike Research/
    # Archive) since it's a small personal list rather than the full catalogue — a 3-month
    # default keeps it useful without needing "Publication Type" to do all the narrowing.
    reports, selections = _apply_report_filters(request, reports, default_date_range='90d')
    paginator, page_obj, reports = _paginate_reports(request, reports)

    if _is_ajax(request):
        response = render(request, 'client_portal/partials/research_cards_page.html', {
            'reports': reports,
            'saved_report_ids': _saved_report_ids(request.user),
        })
        response['X-Has-Next-Page'] = '1' if page_obj.has_next() else '0'
        response['X-Next-Page'] = page_obj.next_page_number() if page_obj.has_next() else ''
        return response

    querystring_params = request.GET.copy()
    querystring_params.pop('page', None)
    querystring = querystring_params.urlencode()

    range_link_params = request.GET.copy()
    range_link_params.pop('page', None)
    range_link_params.pop('date_range', None)
    range_link_base = range_link_params.urlencode()

    publication_type_filters = PublicationType.objects.filter(is_active=True).annotate(
        report_count=Count('reports', filter=Q(reports__id__in=visible_report_ids), distinct=True)
    )

    context = {
        'active_nav': 'saved',
        'reports': reports,
        'report_count': paginator.count,
        'page_obj': page_obj,
        'querystring': querystring,
        'range_link_base': range_link_base,
        'publication_type_filters': publication_type_filters,
        'selected_publication_types': set(publication_type_ids),
        'clear_url': reverse('client_saved_reports') + '?cleared=1',
        'saved_report_ids': _saved_report_ids(request.user),
        'hide_date_range': True,
        **selections,
    }
    context.update(_report_filter_facets(visible_report_ids))
    return render(request, 'client_portal/saved_reports.html', context)


@login_required
def client_help_support(request):
    if not _is_client_role(request.user):
        return redirect('dashboard')

    return render(request, 'client_portal/help_support.html', {
        'active_nav': 'help',
    })


@require_POST
@login_required
def client_toggle_save(request, report_id):
    report = get_object_or_404(_client_reports(request.user), pk=report_id)
    saved_report, created = SavedReport.objects.get_or_create(user=request.user, report=report)
    if not created:
        saved_report.delete()
    return JsonResponse({'saved': created})


@login_required
def client_report_detail(request, report_id):
    if not _is_client_role(request.user):
        return redirect('dashboard')

    report = get_object_or_404(_client_reports(request.user), pk=report_id)

    file_name = report.file_upload.name.lower() if report.file_upload else ''
    is_native_pdf = file_name.endswith('.pdf')
    is_pptx = file_name.endswith('.pptx') or file_name.endswith('.ppt')

    preview_pdf_url = None
    preview_page_count = None
    if is_native_pdf:
        preview_pdf_url = report.file_upload.url
        preview_page_count = _pdf_page_count(report.file_upload.path)
    elif is_pptx:
        pdf_path = _pptx_preview_pdf_path(report)
        if pdf_path:
            preview_pdf_url = settings.MEDIA_URL + f'reports/converted/{pdf_path.name}'
            preview_page_count = _pdf_page_count(pdf_path)

    return render(request, 'client_portal/report_detail.html', {
        'report': report,
        'preview_pdf_url': preview_pdf_url,
        'preview_page_count': preview_page_count,
        'preview_label': 'Presentation' if is_pptx else 'PDF',
        'is_pptx_file': is_pptx and not preview_pdf_url,
        'saved_report_ids': _saved_report_ids(request.user),
    })


@login_required
def client_archive(request):
    if not _is_client_role(request.user):
        return redirect('dashboard')

    # Archive is strictly the older-than-a-year complement of the client-facing sections —
    # anything still shown there (< CLIENT_VISIBILITY_WINDOW old) is excluded here so nothing
    # appears twice.
    all_reports = _client_reports(request.user).filter(
        published_at__isnull=False, published_at__lt=timezone.now() - CLIENT_VISIBILITY_WINDOW
    )
    total_count = all_reports.count()
    visible_report_ids = list(all_reports.values_list('id', flat=True))

    years = sorted({d.year for d in all_reports.values_list('published_at', flat=True)}, reverse=True)
    year_param = request.GET.get('year', '').strip()
    if year_param.isdigit() and int(year_param) in years:
        selected_year = int(year_param)
    else:
        selected_year = years[0] if years else timezone.now().year

    year_reports = all_reports.filter(published_at__year=selected_year)

    publication_type_ids = request.GET.getlist('publication_type')
    if publication_type_ids:
        year_reports = year_reports.filter(publication_type_id__in=publication_type_ids)

    reports, selections = _apply_report_filters(request, year_reports)
    paginator, page_obj, reports = _paginate_reports(request, reports)

    if _is_ajax(request):
        response = render(request, 'client_portal/partials/research_cards_page.html', {
            'reports': reports,
            'saved_report_ids': _saved_report_ids(request.user),
        })
        response['X-Has-Next-Page'] = '1' if page_obj.has_next() else '0'
        response['X-Next-Page'] = page_obj.next_page_number() if page_obj.has_next() else ''
        return response

    querystring_params = request.GET.copy()
    querystring_params.pop('page', None)
    querystring = querystring_params.urlencode()

    year_link_params = request.GET.copy()
    year_link_params.pop('page', None)
    year_link_params.pop('year', None)
    year_link_base = year_link_params.urlencode()

    publication_type_filters = PublicationType.objects.filter(is_active=True).annotate(
        report_count=Count('reports', filter=Q(reports__id__in=visible_report_ids), distinct=True)
    )

    context = {
        'active_nav': 'archive',
        'total_count': total_count,
        'years': years,
        'selected_year': selected_year,
        'year_link_base': year_link_base,
        'clear_url': reverse('client_archive'),
        'reports': reports,
        'report_count': paginator.count,
        'page_obj': page_obj,
        'querystring': querystring,
        'publication_type_filters': publication_type_filters,
        'selected_publication_types': set(publication_type_ids),
        'saved_report_ids': _saved_report_ids(request.user),
        'hide_date_range': True,
        **selections,
    }
    context.update(_report_filter_facets(visible_report_ids))
    return render(request, 'client_portal/archive.html', context)
