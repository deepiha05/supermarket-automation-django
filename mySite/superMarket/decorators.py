from django.http import HttpResponse
from django.shortcuts import redirect

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

            # print('Working:', allowed_roles)
            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name

            if group in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse("You are not Authorised to access this page.")
        return wrapper_func
    return decorator
