from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from modules.client_portal.views import (
    _all_published_current,
    _home_greeting,
    _report_reader_context,
    assemble_home_context,
)
from modules.roles.decorators import permission_required
from modules.users.activity import log_activity

from .models import (
    CARDS_PER_ROW_CHOICES,
    CARDS_PER_ROW_FIELD_BY_TOGGLE,
    CARDS_PER_ROW_FIELDS,
    HEADING_MAX_LENGTH,
    SECTION_HEADINGS,
    TITLE_FIELD_BY_TOGGLE,
    TITLE_FIELDS,
    HomePageSettings,
    normalize_cards_per_row,
)

SECTION_FIELDS = tuple(toggle for toggle, _, _ in SECTION_HEADINGS)

HELP_BY_TOGGLE = {
    'show_featured_research': 'Hero card and featured reports at the top of Home.',
    'show_latest_research': 'Latest Daily Note reports with asset-class filter tabs.',
    'show_weekly_notes': 'Latest Weekly Insight reports with asset-class filter tabs.',
    'show_monthly_notes': 'Latest Monthly Digest reports with asset-class filter tabs.',
    'show_quarterly_notes': 'Latest Quarterly Review reports with asset-class filter tabs.',
    'show_annual_notes': 'Latest Annual Outlook reports with asset-class filter tabs.',
    'show_research_by_asset_class': 'Asset-class headings linking to filtered research.',
}


@permission_required('can_manage_roles')
def home_page_settings_view(request):
    settings_obj = HomePageSettings.load()

    if request.method == 'POST':
        field = request.POST.get('field')
        action = request.POST.get('action')
        if action == 'save_section' and field in SECTION_FIELDS:
            title_field = TITLE_FIELD_BY_TOGGLE[field]
            cards_field = CARDS_PER_ROW_FIELD_BY_TOGGLE[field]
            title = (request.POST.get('title') or '').strip()[:HEADING_MAX_LENGTH]
            cards = normalize_cards_per_row(request.POST.get('cards_per_row'))
            enabled = request.POST.get('enabled') == 'on'
            setattr(settings_obj, title_field, title)
            setattr(settings_obj, cards_field, cards)
            setattr(settings_obj, field, enabled)
            settings_obj.save(update_fields=[title_field, cards_field, field, 'updated_at'])
        elif field in SECTION_FIELDS:
            setattr(settings_obj, field, request.POST.get('value') == 'on')
            settings_obj.save(update_fields=[field, 'updated_at'])
        elif field in TITLE_FIELDS:
            value = (request.POST.get('value') or '').strip()[:HEADING_MAX_LENGTH]
            setattr(settings_obj, field, value)
            settings_obj.save(update_fields=[field, 'updated_at'])
        elif field in CARDS_PER_ROW_FIELDS:
            value = normalize_cards_per_row(request.POST.get('value'))
            setattr(settings_obj, field, value)
            settings_obj.save(update_fields=[field, 'updated_at'])
        else:
            for name in SECTION_FIELDS:
                setattr(settings_obj, name, request.POST.get(name) == 'on')
            settings_obj.save(update_fields=[*SECTION_FIELDS, 'updated_at'])

        log_activity(request, 'updated home page settings')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            payload = {'ok': True}
            if action == 'save_section' and field in SECTION_FIELDS:
                payload['label'] = settings_obj.heading_for_title_field(TITLE_FIELD_BY_TOGGLE[field])
                payload['cards_per_row'] = settings_obj.cards_per_row_for_toggle(field)
                payload['on'] = getattr(settings_obj, field)
            if field in TITLE_FIELDS:
                payload['label'] = settings_obj.heading_for_title_field(field)
            if field in CARDS_PER_ROW_FIELDS:
                payload['cards_per_row'] = settings_obj.cards_per_row_for(field)
            return JsonResponse(payload)
        messages.success(request, 'Home page settings were saved.')
        return redirect('home_page_settings')

    return render(request, 'home_page_settings/settings.html', {
        'active_nav': 'home_page_settings',
        'home_page_settings': settings_obj,
        'heading_max_length': HEADING_MAX_LENGTH,
        'cards_per_row_choices': [value for value, _ in CARDS_PER_ROW_CHOICES],
        'section_toggles': [
            {
                'field': toggle,
                'title_field': title_field,
                'cards_field': CARDS_PER_ROW_FIELD_BY_TOGGLE[toggle],
                'cards_per_row': settings_obj.cards_per_row_for_toggle(toggle),
                'label': settings_obj.heading_for_title_field(title_field),
                'default_label': default_label,
                'help': HELP_BY_TOGGLE[toggle],
                'on': getattr(settings_obj, toggle),
                'uses_card_grid': toggle != 'show_featured_research',
            }
            for toggle, title_field, default_label in SECTION_HEADINGS
        ],
    })


@permission_required('can_manage_roles')
def client_home_preview(request):
    context, ajax_response = assemble_home_context(
        request,
        _all_published_current(),
        home_url_name='client_home_preview',
        is_home_preview=True,
    )
    if ajax_response:
        return ajax_response

    context.update({
        'active_nav': 'home_page_preview',
        'new_since_login': 0,
        'greeting': _home_greeting(),
    })
    return render(request, 'home_page_settings/preview.html', context)


@permission_required('can_manage_roles')
def client_home_preview_report(request, report_id):
    report = get_object_or_404(
        _all_published_current().select_related('author', 'publication_type'),
        pk=report_id,
    )
    context = _report_reader_context(report, is_home_preview=True)
    context['active_nav'] = 'home_page_preview'
    return render(request, 'client_portal/report_detail.html', context)
