from django.contrib import messages
from django.shortcuts import redirect, render

from modules.client_portal.views import _all_published_current, _home_greeting, assemble_home_context
from modules.roles.decorators import permission_required
from modules.users.activity import log_activity

from .models import HomePageSettings

SECTION_FIELDS = (
    'show_featured_research',
    'show_latest_research',
    'show_weekly_notes',
    'show_monthly_notes',
    'show_quarterly_notes',
    'show_annual_notes',
    'show_research_by_asset_class',
)

SECTION_TOGGLES = (
    ('show_featured_research', 'Featured Research', 'Hero card and featured reports at the top of Home.'),
    ('show_latest_research', 'Daily Note', 'Latest Daily Note reports with asset-class filter tabs.'),
    ('show_weekly_notes', 'Weekly Insight', 'Latest Weekly Insight reports with asset-class filter tabs.'),
    ('show_monthly_notes', 'Monthly Digest', 'Latest Monthly Digest reports with asset-class filter tabs.'),
    ('show_quarterly_notes', 'Quarterly Review', 'Latest Quarterly Review reports with asset-class filter tabs.'),
    ('show_annual_notes', 'Annual Outlook', 'Latest Annual Outlook reports with asset-class filter tabs.'),
    ('show_research_by_asset_class', 'Research by Asset Class', 'Asset-class headings linking to filtered research.'),
)


@permission_required('can_manage_roles')
def home_page_settings_view(request):
    settings_obj = HomePageSettings.load()

    if request.method == 'POST':
        for field in SECTION_FIELDS:
            setattr(settings_obj, field, request.POST.get(field) == 'on')
        settings_obj.save(update_fields=[*SECTION_FIELDS, 'updated_at'])

        log_activity(request, 'updated home page settings')
        messages.success(request, 'Home page settings were saved.')
        return redirect('home_page_settings')

    return render(request, 'home_page_settings/settings.html', {
        'active_nav': 'home_page_settings',
        'home_page_settings': settings_obj,
        'section_toggles': [
            {
                'field': field,
                'label': label,
                'help': help_text,
                'on': getattr(settings_obj, field),
            }
            for field, label, help_text in SECTION_TOGGLES
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
