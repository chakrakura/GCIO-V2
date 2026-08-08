from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from modules.users.activity import log_activity


def _is_internal(user):
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.role and profile.role.is_internal)


def _landing_view(user):
    role = user.profile.role
    if role.is_admin_role:
        return 'dashboard'
    if role.can_manage_content:
        return 'report_list'
    return 'profile'


def login_view(request):
    if request.user.is_authenticated:
        if _is_internal(request.user):
            return redirect(_landing_view(request.user))
        return redirect('client_home')

    error = None
    submitted_email = ''

    if request.method == 'POST':
        submitted_email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = None
        try:
            user_obj = User.objects.get(email__iexact=submitted_email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            previous_login = user.last_login
            login(request, user)
            request.session['previous_login'] = previous_login.isoformat() if previous_login else None
            log_activity(request, 'logged in')
            if _is_internal(user):
                return redirect(_landing_view(user))
            return redirect('client_home')

        error = 'Invalid email or password. Please try again.'

    return render(request, 'login/login.html', {
        'error': error,
        'submitted_email': submitted_email,
    })


def logout_view(request):
    log_activity(request, 'logged out')
    logout(request)
    return redirect('login')
