from django.shortcuts import render, redirect
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect

def _get_dashboard_redirect(user):
    if user.is_superuser or user.is_staff:
        return reverse('admin_dashboard')

    if user.groups.filter(name='Verifier').exists():
        return reverse('verifier_dashboard')

    if user.groups.filter(name='Manager').exists():
        return reverse('admin_dashboard')

    return reverse('client_dashboard')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Ensure new/ungrouped users get a default client group so role redirect works.
            try:
                from django.contrib.auth.models import Group
                if not (user.is_staff or user.is_superuser) and not user.groups.exists():
                    group, created = Group.objects.get_or_create(name='Client')
                    user.groups.add(group)
                    if created:
                        logger.info("Created default 'Client' group and assigned to %s", username)
            except Exception:
                logger.exception('Error ensuring client group for user %s', username)

            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                logger.info('Redirecting to next: %s', next_url)
                return redirect(next_url)

            target = _get_dashboard_redirect(user)
            logger.info('User %s logged in, redirecting to %s', username, target)
            messages.success(request, 'Signed in successfully.')
            return redirect(target)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')

def register_view(request):
    if request.method == 'POST':
        from kyc.forms import UserRoleSelectionForm
        form = UserRoleSelectionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('client_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        from kyc.forms import UserRoleSelectionForm
        form = UserRoleSelectionForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@csrf_protect
@login_required(login_url='login')
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('login')
