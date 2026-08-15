from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from gcio.pagination import paginate
from modules.organizations.models import Organization
from modules.roles.decorators import permission_required
from modules.roles.models import Role

from .activity import log_activity
from .forms import ProfileSelfForm, StyledPasswordChangeForm, UserForm, generate_temp_password
from .models import ActivityLog, Profile

IMPERSONATOR_SESSION_KEY = 'impersonator_id'


def _profile_base_template(user):
    """Client users get the client-portal shell; internal staff get the admin console shell."""
    role = getattr(user.profile, 'role', None)
    is_client = bool(role and not role.is_internal)
    return 'client_portal/base_client.html' if is_client else 'console/base.html'


def _get_filter_list(request, param_name):
    raw_list = request.GET.getlist(param_name)
    cleaned = []
    for item in raw_list:
        for sub in str(item).split(','):
            val = sub.strip()
            if val and val != '__none__' and val not in cleaned:
                cleaned.append(val)
    return cleaned


@permission_required('can_manage_users')
def user_list(request):
    users = User.objects.select_related('profile', 'profile__role').prefetch_related('profile__organizations').order_by('first_name', 'last_name')

    query = request.GET.get('q', '').strip()
    if query:
        users = users.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )

    status_list = _get_filter_list(request, 'status')
    if 'active' in status_list and 'inactive' not in status_list:
        users = users.filter(is_active=True)
    elif 'inactive' in status_list and 'active' not in status_list:
        users = users.filter(is_active=False)

    role_ids = _get_filter_list(request, 'role')
    if role_ids:
        users = users.filter(profile__role_id__in=role_ids)

    org_ids = _get_filter_list(request, 'org')
    if org_ids:
        users = users.filter(profile__organizations__id__in=org_ids)

    users = users.distinct()
    total_count = users.count()
    page_obj, base_qs = paginate(request, users)

    roles = Role.objects.all().order_by('name')
    organizations = Organization.objects.all()

    status_summary = ", ".join([s.capitalize() for s in status_list if s in ['active', 'inactive']])
    role_summary = ", ".join([r.name for r in roles if str(r.id) in role_ids])
    org_summary = ", ".join([o.name for o in organizations if str(o.id) in org_ids])

    return render(request, 'users/user_list.html', {
        'active_nav': 'users',
        'users': page_obj.object_list,
        'page_obj': page_obj,
        'base_qs': base_qs,
        'query': query,
        'status_list': status_list,
        'status': status_list[0] if status_list else '',
        'status_summary': status_summary,
        'role_ids': role_ids,
        'role_id': role_ids[0] if role_ids else '',
        'role_summary': role_summary,
        'org_ids': org_ids,
        'org_id': org_ids[0] if org_ids else '',
        'org_summary': org_summary,
        'roles': roles,
        'organizations': organizations,
        'total_count': total_count,
    })


@permission_required('can_manage_users')
def user_add(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            user, temp_password = form.save()
            log_activity(request, 'created user', user.get_full_name() or user.email)
            if temp_password:
                messages.success(
                    request,
                    f'{user.get_full_name() or user.email} was created. Temporary password: {temp_password}'
                )
            else:
                messages.success(request, f'{user.get_full_name() or user.email} was created.')
            return redirect('user_list')
    else:
        form = UserForm()

    return render(request, 'users/user_form.html', {
        'active_nav': 'users',
        'form': form,
        'is_edit': False,
    })


@permission_required('can_manage_users')
def user_edit(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = Profile.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, editing_user=target_user)
        if form.is_valid():
            form.save()
            log_activity(request, 'updated user', target_user.get_full_name() or target_user.email)
            messages.success(request, f'{target_user.get_full_name() or target_user.email} was updated.')
            return redirect('user_list')
    else:
        form = UserForm(initial={
            'first_name': target_user.first_name,
            'last_name': target_user.last_name,
            'email': target_user.email,
            'organizations': profile.organizations.all(),
            'role': profile.role,
        }, editing_user=target_user)

    return render(request, 'users/user_form.html', {
        'active_nav': 'users',
        'form': form,
        'is_edit': True,
        'target_user': target_user,
    })


@permission_required('can_manage_users')
def user_reset_password(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        temp_password = generate_temp_password()
        target_user.set_password(temp_password)
        target_user.save()
        log_activity(request, 'reset password for', target_user.get_full_name() or target_user.email)
        messages.success(
            request,
            f'Password reset for {target_user.get_full_name() or target_user.email}. New temporary password: {temp_password}'
        )
    return redirect('user_list')


@permission_required('can_manage_users')
def user_toggle_status(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        if target_user == request.user:
            messages.error(request, "You can't deactivate your own account.")
        else:
            target_user.is_active = not target_user.is_active
            target_user.save()
            state = 'activated' if target_user.is_active else 'deactivated'
            log_activity(request, f'{state} user', target_user.get_full_name() or target_user.email)
            messages.success(request, f'{target_user.get_full_name() or target_user.email} was {state}.')
    return redirect('user_list')


@permission_required('can_manage_users')
def user_impersonate(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)

    if request.method != 'POST':
        return redirect('user_list')

    if target_user == request.user:
        messages.error(request, "You're already signed in as yourself.")
        return redirect('user_list')

    if target_user.is_superuser:
        messages.error(request, "You can't log in as another Super Admin.")
        return redirect('user_list')

    if not target_user.is_active:
        messages.error(request, "You can't log in as a deactivated user.")
        return redirect('user_list')

    admin_user = request.user
    log_activity(request, 'logged in as', target_user.get_full_name() or target_user.email, actor=admin_user)
    login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')
    request.session[IMPERSONATOR_SESSION_KEY] = admin_user.id
    messages.success(request, f'You are now viewing as {target_user.get_full_name() or target_user.email}.')
    return redirect('login')


def stop_impersonating(request):
    admin_id = request.session.get(IMPERSONATOR_SESSION_KEY)
    if not admin_id:
        return redirect('login')

    admin_user = User.objects.filter(pk=admin_id, is_active=True).first()
    if not admin_user:
        messages.error(request, "Couldn't return to your admin account.")
        return redirect('login')

    log_activity(request, 'returned from viewing as', request.user.get_full_name() or request.user.email, actor=admin_user)

    del request.session[IMPERSONATOR_SESSION_KEY]
    login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, 'You are back in your own account.')
    return redirect('user_list')


@login_required
def profile_view(request):
    if request.method == 'POST':
        profile_form = ProfileSelfForm(request.POST, request.FILES, editing_user=request.user)
        if profile_form.is_valid():
            profile_form.save()
            log_activity(request, 'updated own profile')
            messages.success(request, 'Your profile was updated.')
            return redirect('profile')
    else:
        profile_form = ProfileSelfForm(editing_user=request.user, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        })

    return render(request, 'users/profile.html', {
        'active_nav': 'profile',
        'profile_form': profile_form,
        'base_template': _profile_base_template(request.user),
    })


@login_required
def profile_password_view(request):
    if request.method == 'POST':
        password_form = StyledPasswordChangeForm(user=request.user, data=request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            log_activity(request, 'changed own password')
            messages.success(request, 'Your password was changed.')
            return redirect('profile_password')
    else:
        password_form = StyledPasswordChangeForm(user=request.user)

    return render(request, 'users/profile_password.html', {
        'active_nav': 'profile',
        'password_form': password_form,
        'base_template': _profile_base_template(request.user),
    })


@permission_required('can_view_logs')
def admin_actions_view(request):
    logs = ActivityLog.objects.select_related('actor').all()

    user_id = request.GET.get('user', '').strip()
    if user_id:
        logs = logs.filter(actor_id=user_id)

    has_custom_dates = 'date_from' in request.GET or 'date_to' in request.GET
    today = timezone.localdate()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    if not has_custom_dates:
        date_from = (today - timedelta(days=7)).isoformat()
        date_to = today.isoformat()

    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)

    actor_ids = ActivityLog.objects.exclude(actor__isnull=True).values_list('actor_id', flat=True).distinct()
    users = User.objects.filter(id__in=actor_ids).order_by('first_name', 'last_name')

    total_count = logs.count()
    page_obj, base_qs = paginate(request, logs)

    return render(request, 'users/admin_actions.html', {
        'active_nav': 'logs',
        'logs': page_obj.object_list,
        'page_obj': page_obj,
        'base_qs': base_qs,
        'total_count': total_count,
        'users': users,
        'selected_user_id': user_id,
        'date_from': date_from,
        'date_to': date_to,
        'has_filters': bool(user_id) or has_custom_dates,
    })
