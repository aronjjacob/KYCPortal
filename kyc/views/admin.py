from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from kyc.models import KYCProfile, KYCDocument

from ..forms import UserCreateForm, UserUpdateForm

User = get_user_model()

@login_required
def admin_dashboard(request):
    today = timezone.now().date()
    
    # Get real statistics from the database
    pending_count = KYCProfile.objects.filter(
        status__in=['Pending', 'Under Review']
    ).count()
    
    approved_today_count = KYCProfile.objects.filter(
        status='Approved',
        created_at__date=today
    ).count()
    
    rejected_count = KYCProfile.objects.filter(
        status='Rejected'
    ).count()
    
    # Count ALL registered users (not just those with KYC profiles)
    total_users = User.objects.count()
    
    context = {
        'pending_count': pending_count,
        'approved_today_count': approved_today_count,
        'rejected_count': rejected_count,
        'total_users': total_users,
    }
    
    return render(request, "kyc/admin/admin_dashboard.html", context)

@login_required
def user_management(request):
    users = User.objects.all().prefetch_related('groups').order_by('username')
    
    edit_user = None
    edit_form = None
    create_form = UserCreateForm()

    role_filter = request.GET.get('role', 'all')
    search_query = request.GET.get('search', '')
    
    if role_filter == 'admin':
        users = users.filter(is_superuser=True)
    elif role_filter == 'verifier':
        users = users.filter(groups__name='verifier').distinct()
    elif role_filter == 'applicant':
        users = users.exclude(is_superuser=True).exclude(groups__name='verifier').distinct()

    if search_query:
        users = users.filter(username__icontains=search_query) | users.filter(email__icontains=search_query)
        users = users.distinct()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            create_form = UserCreateForm(request.POST)
            if create_form.is_valid():
                create_form.save()
                messages.success(request, 'User created successfully.')
                return redirect('user_management')
            messages.error(request, 'Please correct the errors in the create form.')
        
        elif action == 'update':
            user_id = request.POST.get('user_id')
            edit_user = get_object_or_404(User, pk=user_id)
            edit_form = UserUpdateForm(request.POST, instance=edit_user)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'User updated successfully.')
                return redirect('user_management')
            messages.error(request, 'Please correct the errors in the update form.')
        
        elif action == 'delete':
            user_id = request.POST.get('user_id')
            if str(request.user.pk) == str(user_id):
                messages.error(request, 'You cannot delete your own account.')
            else:
                delete_user = get_object_or_404(User, pk=user_id)
                delete_user.delete()
                messages.success(request, 'User deleted successfully.')
            return redirect('user_management')
    
    if request.method == 'GET':
        edit_id = request.GET.get('edit')
        if edit_id:
            edit_user = get_object_or_404(User, pk=edit_id)
            edit_form = UserUpdateForm(instance=edit_user)

    thirty_days_ago = timezone.now() - timedelta(days=30)
    previous_month = thirty_days_ago - timedelta(days=30)
    active_users_count = User.objects.filter(is_active=True).count()
    growth_percentage = 0  # Calculate based on your needs
    
    
    return render(request, 'kyc/user_management.html', {
        'users': users,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'staff_users': users.filter(is_staff=True).count(),
        'super_users': users.filter(is_superuser=True).count(),
        'create_form': create_form,
        'edit_user': edit_user,
        'edit_form': edit_form,
        'growth_percentage': growth_percentage,
        'active_users': active_users_count,
        'pending_invitations': 0,
        'security_alerts': 0,
        'role_filter': role_filter,
        'search_query': search_query,
    })


@login_required
def document_review(request):
    return render(request, "kyc/document_review.html")
