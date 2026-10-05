from django.shortcuts import redirect, render

def unauthenticated_manager(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/manager_page1')
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_func

def unauthenticated_employee(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/employee_page1')
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_func

def unauthenticated_salesClerk(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/salesClerk_page1')
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_func

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):

            # Superusers, and users in any of the allowed groups, may see the page
            if request.user.is_superuser or request.user.groups.filter(name__in=allowed_roles).exists():
                return view_func(request, *args, **kwargs)
            else:
                return render(request, 'unauthorised_page.html', status=403)
        return wrapper_func
    return decorator
