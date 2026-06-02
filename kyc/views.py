from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

from .decorators import group_required
from .forms import KYCProfileForm, KYCDocumentForm, UserCreateForm, UserUpdateForm
from .models import KYCProfile, KYCDocument


# ========================
# CLIENT SIDE
# ========================

@login_required
# @group_required('Client')
def client_dashboard(request):
    profile = KYCProfile.objects.filter(user=request.user).first()

    return render(request, 'kyc/client/client_dashboard.html', {
        'profile': profile
    })


@login_required
# @group_required('Client')
def kyc_upload(request):
    existing_profile = KYCProfile.objects.filter(user=request.user).first()

    if request.method == 'POST':
        profile_form = KYCProfileForm(request.POST, instance=existing_profile)
        document_form = KYCDocumentForm(request.POST, request.FILES)

        if profile_form.is_valid() and document_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.status = 'Pending'
            profile.save()

            document = document_form.save(commit=False)
            document.profile = profile
            document.save()

            messages.success(request, 'Your KYC documents have been submitted successfully.')
            return redirect('client_dashboard')
        else:
            messages.error(request, 'Please check your form and try again.')

    else:
        profile_form = KYCProfileForm(instance=existing_profile)
        document_form = KYCDocumentForm()

    return render(request, 'kyc/kyc_upload.html', {
        'profile_form': profile_form,
        'document_form': document_form
    })


@login_required
# @group_required('Client')
def kyc_documents(request):
    profile = KYCProfile.objects.filter(user=request.user).first()
    documents = []

    if profile:
        documents = profile.documents.all().order_by('-uploaded_at')

    return render(request, 'kyc/kyc_documents.html', {
        'profile': profile,
        'documents': documents
    })


@login_required
# @group_required('Client')
def kyc_liveness(request):
    profile = KYCProfile.objects.filter(user=request.user).first()

    return render(request, 'kyc/kyc_liveness.html', {
        'profile': profile
    })


@login_required
# @group_required('Client')
def kyc_finalize(request):
    profile = KYCProfile.objects.filter(user=request.user).first()
    documents = []

    if profile:
        documents = profile.documents.all().order_by('-uploaded_at')

    return render(request, 'kyc/kyc_finalize.html', {
        'profile': profile,
        'documents': documents
    })


@login_required
# @group_required('Client')
def kyc_status(request):
    profile = KYCProfile.objects.filter(user=request.user).first()
    documents = []

    if profile:
        documents = profile.documents.all().order_by('-uploaded_at')

    return render(request, 'kyc/kyc_status.html', {
        'profile': profile,
        'documents': documents
    })


# ========================
# ADMIN / VERIFIER SIDE
# ========================

@login_required
# @group_required('Verifier', 'Manager')
def admin_dashboard(request):
    profiles = KYCProfile.objects.all().order_by('-created_at')

    total_profiles = profiles.count()
    pending_count = profiles.filter(status='Pending').count()
    approved_count = profiles.filter(status='Approved').count()
    rejected_count = profiles.filter(status='Rejected').count()
    under_review_count = profiles.filter(status='Under Review').count()

    return render(request, 'kyc/admin_dashboard.html', {
        'profiles': profiles,
        'total_profiles': total_profiles,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'under_review_count': under_review_count,
    })


@login_required
# @group_required('Verifier', 'Manager')
def user_management(request):
    User = get_user_model()
    users = User.objects.all().prefetch_related('groups').order_by('username')

    edit_user = None
    edit_form = None
    create_form = UserCreateForm()

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

    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    staff_users = users.filter(is_staff=True).count()
    super_users = users.filter(is_superuser=True).count()

    return render(request, 'kyc/user_management.html', {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'super_users': super_users,
        'create_form': create_form,
        'edit_user': edit_user,
        'edit_form': edit_form,
    })


@login_required
# @group_required('Verifier', 'Manager')
def document_review(request, pk):
    profile = get_object_or_404(KYCProfile, pk=pk)
    documents = profile.documents.all().order_by('-uploaded_at')
    first_document = documents.first()

    if request.method == 'POST':
        action = request.POST.get('action')
        remarks = request.POST.get('remarks')

        if action == 'approve':
            profile.status = 'Approved'
        elif action == 'reject':
            profile.status = 'Rejected'
        elif action == 'under_review':
            profile.status = 'Under Review'
        elif action == 'resubmission':
            profile.status = 'Resubmission Required'
        else:
            messages.error(request, 'Invalid action.')
            return redirect('document_review', pk=profile.pk)

        profile.save()

        for document in documents:
            document.remarks = remarks
            document.save()

        messages.success(request, 'KYC application has been updated successfully.')
        return redirect('admin_dashboard')

    return render(request, 'kyc/document_review.html', {
        'profile': profile,
        'documents': documents,
        'first_document': first_document,
    })


@login_required
def document_detail(request, pk):
    if request.user.is_superuser or request.user.groups.filter(name__in=['Verifier', 'Manager']).exists():
        document = get_object_or_404(KYCDocument, pk=pk)

    elif request.user.groups.filter(name='Client').exists():
        document = get_object_or_404(
            KYCDocument,
            pk=pk,
            profile__user=request.user
        )

    else:
        raise PermissionDenied

    return render(request, 'kyc/document_detail.html', {
        'document': document
    })


@login_required
# @group_required('Manager')
def bulk_update_status(request):
    if request.method == 'POST':
        selected_profiles = request.POST.getlist('selected_profiles')
        new_status = request.POST.get('new_status')

        allowed_statuses = [
            'Approved',
            'Rejected',
            'Under Review',
            'Resubmission Required'
        ]

        if selected_profiles and new_status in allowed_statuses:
            KYCProfile.objects.filter(id__in=selected_profiles).update(status=new_status)
            messages.success(request, 'Selected KYC records have been updated.')
        else:
            messages.error(request, 'Please select records and a valid status.')

    return redirect('admin_dashboard')