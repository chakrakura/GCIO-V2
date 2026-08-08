from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from gcio.pagination import paginate
from modules.users.activity import log_activity

from .decorators import permission_required
from .forms import RoleForm
from .models import Role


@permission_required('can_manage_roles')
def role_list(request):
    roles = Role.objects.all().order_by('name')
    page_obj, base_qs = paginate(request, roles)
    return render(request, 'roles/role_list.html', {
        'active_nav': 'roles',
        'roles': page_obj.object_list,
        'page_obj': page_obj,
        'base_qs': base_qs,
    })


@permission_required('can_manage_roles')
def role_add(request):
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            log_activity(request, 'created role', role.name)
            messages.success(request, f'Role "{role.name}" was created.')
            return redirect('role_list')
    else:
        form = RoleForm()

    return render(request, 'roles/role_form.html', {
        'active_nav': 'roles',
        'form': form,
        'is_edit': False,
    })


@permission_required('can_manage_roles')
def role_edit(request, role_id):
    role = get_object_or_404(Role, pk=role_id)

    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            log_activity(request, 'updated role', role.name)
            messages.success(request, f'Role "{role.name}" was updated.')
            return redirect('role_list')
    else:
        form = RoleForm(instance=role)

    return render(request, 'roles/role_form.html', {
        'active_nav': 'roles',
        'form': form,
        'is_edit': True,
        'role': role,
    })


@permission_required('can_manage_roles')
def role_delete(request, role_id):
    role = get_object_or_404(Role, pk=role_id)
    if request.method == 'POST':
        if role.is_system:
            messages.error(request, f'"{role.name}" is a built-in role and can\'t be deleted.')
        elif role.user_count:
            messages.error(request, f'"{role.name}" is assigned to {role.user_count} user(s). Reassign them first.')
        else:
            role.delete()
            log_activity(request, 'deleted role', role.name)
            messages.success(request, f'Role "{role.name}" was deleted.')
    return redirect('role_list')
