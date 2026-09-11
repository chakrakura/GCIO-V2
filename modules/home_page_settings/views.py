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
    HEADING_MAX_LENGTH,
    SECTION_HEADINGS,
    TITLE_FIELD_BY_TOGGLE,
    TITLE_FIELDS,
    TOP_NOTES_FIELD_BY_TOGGLE,
    TOP_NOTES_FIELDS,
    TOP_NOTES_MAX,
    TOP_NOTES_MIN,
    HomePageSettings,
    normalize_top_notes,
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
            title = (request.POST.get('title') or '').strip()[:HEADING_MAX_LENGTH]
            enabled = request.POST.get('enabled') == 'on'
            setattr(settings_obj, title_field, title)
            setattr(settings_obj, field, enabled)
            update_fields = [title_field, field, 'updated_at']
            if field in TOP_NOTES_FIELD_BY_TOGGLE:
                top_field = TOP_NOTES_FIELD_BY_TOGGLE[field]
                setattr(settings_obj, top_field, normalize_top_notes(request.POST.get('top_notes')))
                update_fields.insert(-1, top_field)
            settings_obj.save(update_fields=update_fields)
        elif field in SECTION_FIELDS:
            setattr(settings_obj, field, request.POST.get('value') == 'on')
            settings_obj.save(update_fields=[field, 'updated_at'])
        elif field in TITLE_FIELDS:
            value = (request.POST.get('value') or '').strip()[:HEADING_MAX_LENGTH]
            setattr(settings_obj, field, value)
            settings_obj.save(update_fields=[field, 'updated_at'])
        elif field in TOP_NOTES_FIELDS:
            value = normalize_top_notes(request.POST.get('value'))
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
                payload['on'] = getattr(settings_obj, field)
                if field in TOP_NOTES_FIELD_BY_TOGGLE:
                    payload['top_notes'] = settings_obj.top_notes_for_toggle(field)
            if field in TITLE_FIELDS:
                payload['label'] = settings_obj.heading_for_title_field(field)
            if field in TOP_NOTES_FIELDS:
                payload['top_notes'] = settings_obj.top_notes_for(field)
            return JsonResponse(payload)
        messages.success(request, 'Home page settings were saved.')
        return redirect('home_page_settings')

    return render(request, 'home_page_settings/settings.html', {
        'active_nav': 'home_page_settings',
        'home_page_settings': settings_obj,
        'heading_max_length': HEADING_MAX_LENGTH,
        'top_notes_min': TOP_NOTES_MIN,
        'top_notes_max': TOP_NOTES_MAX,
        'section_toggles': [
            {
                'field': toggle,
                'title_field': title_field,
                'top_notes_field': TOP_NOTES_FIELD_BY_TOGGLE.get(toggle, ''),
                'top_notes': settings_obj.top_notes_for_toggle(toggle) if toggle in TOP_NOTES_FIELD_BY_TOGGLE else None,
                'label': settings_obj.heading_for_title_field(title_field),
                'default_label': default_label,
                'help': HELP_BY_TOGGLE[toggle],
                'on': getattr(settings_obj, toggle),
                'uses_top_notes': toggle in TOP_NOTES_FIELD_BY_TOGGLE,
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
