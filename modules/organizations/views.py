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


@permission_required('can_manage_organizations')
def organization_list(request):
    organizations = Organization.objects.select_related('country').order_by('name')

    query = request.GET.get('q', '').strip()
    if query:
        organizations = organizations.filter(Q(name__icontains=query))

    status = request.GET.get('status', '').strip()
    if status == 'active':
        organizations = organizations.filter(is_active=True)
    elif status == 'inactive':
        organizations = organizations.filter(is_active=False)

    country_id = request.GET.get('country', '').strip()
    if country_id:
        organizations = organizations.filter(country_id=country_id)

    user_id = request.GET.get('user', '').strip()
    if user_id:
        organizations = organizations.filter(members__user_id=user_id).distinct()

    total_count = organizations.count()
    page_obj, base_qs = paginate(request, organizations)

    return render(request, 'organizations/organization_list.html', {
        'active_nav': 'organizations',
        'organizations': page_obj.object_list,
        'page_obj': page_obj,
        'base_qs': base_qs,
        'query': query,
        'status': status,
        'country_id': country_id,
        'user_id': user_id,
        'countries': CountryRegion.objects.filter(is_active=True),
        'users': User.objects.filter(profile__organizations__isnull=False).distinct().order_by('first_name', 'last_name'),
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
