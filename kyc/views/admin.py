from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def admin_dashboard(request):
    return render(request, "kyc/admin/admin_dashboard.html")

@login_required
def user_management(request):
    return render(request, "kyc/user_management.html")


@login_required
def document_review(request):
    return render(request, "kyc/document_review.html")
