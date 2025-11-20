from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden


def role_required(roles):
    def check(user):
        return user.is_authenticated and user.role in roles

    def decorator(view_func):
        decorated = user_passes_test(check)(view_func)

        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or request.user.role not in roles:
                return HttpResponseForbidden("No tienes permiso para acceder a esta sección.")
            return decorated(request, *args, **kwargs)

        return _wrapped_view

    return decorator
