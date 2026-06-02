from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from kyc.models import KYCProfile, KYCDocument

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
    return render(request, "kyc/user_management.html")


@login_required
def document_review(request):
    return render(request, "kyc/document_review.html")
