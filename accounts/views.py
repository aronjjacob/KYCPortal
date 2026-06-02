from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.views.decorators.csrf import csrf_protect


def _user_role(user) -> str:
    if user.is_superuser:
        return 'superadmin'
    if user.is_staff:
        return 'admin'
    return 'client'


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            role = _user_role(user)
            request.session['user_role'] = role

            # Superusers/admins go to admin dashboard; everyone else is treated as a client.
            if role in ('superadmin', 'admin'):
                return redirect('admin_dashboard')
            return redirect('client_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/register.html')
        
        user = User.objects.create_user(username=username, email=email, password=password)

        # Mark newly registered users as clients.
        client_group, _ = Group.objects.get_or_create(name='Client')
        user.groups.add(client_group)

        login(request, user)
        request.session['user_role'] = _user_role(user)
        return redirect('client_dashboard')
    
    return render(request, 'accounts/register.html')

@csrf_protect
@login_required(login_url='login')
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('login')


@login_required(login_url='login')
def admin_dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('client_dashboard')
    return render(request, 'kyc/admin_dashboard.html')


@login_required(login_url='login')
def admin_management(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('client_dashboard')
    return render(request, 'kyc/admin/admin_management.html')
