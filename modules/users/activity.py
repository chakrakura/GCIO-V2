from .models import ActivityLog


def log_activity(request, action, target='', actor=None):
    if actor is None:
        actor = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    ActivityLog.objects.create(actor=actor, action=action, target=target)
