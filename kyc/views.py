from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .decorators import group_required
from .forms import KYCProfileForm, KYCDocumentForm


@login_required
@group_required('Client')
def kyc_upload(request):
    if request.method == 'POST':
        profile_form = KYCProfileForm(request.POST)
        document_form = KYCDocumentForm(request.POST, request.FILES)

        if profile_form.is_valid() and document_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()

            document = document_form.save(commit=False)
            document.profile = profile
            document.save()

            return redirect('client_dashboard')
    else:
        profile_form = KYCProfileForm()
        document_form = KYCDocumentForm()

    return render(request, 'kyc/kyc_upload.html', {
        'profile_form': profile_form,
        'document_form': document_form
    })
    
    
@login_required
def client_dashboard(request):
    return render(request, 'kyc/client_dashboard.html')


@login_required
def admin_dashboard(request):
    return render(request, 'kyc/admin/admin_dashboard.html')


@login_required
def document_review(request):
    return render(request, 'kyc/document_review.html')