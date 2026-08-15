from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from gcio.pagination import paginate
from modules.roles.decorators import permission_required
from modules.taxonomy.models import CountryRegion
from modules.users.activity import log_activity

from .forms import OrganizationForm
from .models import Organization


def _get_filter_list(request, param_name):
    raw_list = request.GET.getlist(param_name)
    cleaned = []
    for item in raw_list:
        for sub in str(item).split(','):
            val = sub.strip()
            if val and val != '__none__' and val not in cleaned:
                cleaned.append(val)
    return cleaned


@permission_required('can_manage_organizations')
def organization_list(request):
    organizations = Organization.objects.select_related('country').order_by('name')

    query = request.GET.get('q', '').strip()
    if query:
        organizations = organizations.filter(Q(name__icontains=query))

    status_list = _get_filter_list(request, 'status')
    if 'active' in status_list and 'inactive' not in status_list:
        organizations = organizations.filter(is_active=True)
    elif 'inactive' in status_list and 'active' not in status_list:
        organizations = organizations.filter(is_active=False)

    country_ids = _get_filter_list(request, 'country')
    if country_ids:
        organizations = organizations.filter(country_id__in=country_ids)

    user_ids = _get_filter_list(request, 'user')
    if user_ids:
        organizations = organizations.filter(members__user_id__in=user_ids)

    organizations = organizations.distinct()
    total_count = organizations.count()
    page_obj, base_qs = paginate(request, organizations)

    countries = CountryRegion.objects.filter(is_active=True)
    users = User.objects.filter(profile__organizations__isnull=False).distinct().order_by('first_name', 'last_name')

    status_summary = ", ".join([s.capitalize() for s in status_list if s in ['active', 'inactive']])
    country_summary = ", ".join([c.name for c in countries if str(c.id) in country_ids])
    user_summary = ", ".join([u.get_full_name() or u.username for u in users if str(u.id) in user_ids])

    return render(request, 'organizations/organization_list.html', {
        'active_nav': 'organizations',
        'organizations': page_obj.object_list,
        'page_obj': page_obj,
        'base_qs': base_qs,
        'query': query,
        'status_list': status_list,
        'status': status_list[0] if status_list else '',
        'status_summary': status_summary,
        'country_ids': country_ids,
        'country_id': country_ids[0] if country_ids else '',
        'country_summary': country_summary,
        'user_ids': user_ids,
        'user_id': user_ids[0] if user_ids else '',
        'user_summary': user_summary,
        'countries': countries,
        'users': users,
        'total_count': total_count,
    })


@permission_required('can_manage_organizations')
def organization_add(request):
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            org = form.save()
            log_activity(request, 'created organisation', org.name)
            messages.success(request, f'Organisation "{org.name}" was created.')
            return redirect('organization_list')
    else:
        form = OrganizationForm()

    return render(request, 'organizations/organization_form.html', {
        'active_nav': 'organizations',
        'form': form,
        'is_edit': False,
    })


@permission_required('can_manage_organizations')
def organization_edit(request, org_id):
    org = get_object_or_404(Organization, pk=org_id)

    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=org)
        if form.is_valid():
            form.save()
            log_activity(request, 'updated organisation', org.name)
            messages.success(request, f'Organisation "{org.name}" was updated.')
            return redirect('organization_list')
    else:
        form = OrganizationForm(instance=org)

    return render(request, 'organizations/organization_form.html', {
        'active_nav': 'organizations',
        'form': form,
        'is_edit': True,
        'org': org,
    })


@permission_required('can_manage_organizations')
def organization_toggle_status(request, org_id):
    org = get_object_or_404(Organization, pk=org_id)
    if request.method == 'POST':
        org.is_active = not org.is_active
        org.save()
        state = 'activated' if org.is_active else 'deactivated'
        log_activity(request, f'{state} organisation', org.name)
        messages.success(request, f'Organisation "{org.name}" was {state}.')
    return redirect('organization_list')
