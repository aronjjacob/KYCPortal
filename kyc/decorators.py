from django.contrib.auth.decorators import user_passes_test
from functools import wraps


def group_required(group_name):
    """
    Decorator to check if user belongs to a specific group.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.groups.filter(name=group_name).exists():
                    return view_func(request, *args, **kwargs)
            from django.shortcuts import redirect
            return redirect('login')
        return wrapper
    return decorator
