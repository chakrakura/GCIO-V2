from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def permission_required(*flags):
    """Require the logged-in user's role to have every one of the given boolean flags
    (e.g. 'can_manage_users', 'is_internal') set True on modules.roles.models.Role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            profile = getattr(request.user, 'profile', None)
            role = getattr(profile, 'role', None)
            if not role or not all(getattr(role, flag, False) for flag in flags):
                messages.error(request, "You don't have access to this page.")
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
