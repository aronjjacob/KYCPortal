def document_review(request):
def user_management(request):
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.views import View
from django.views.generic import TemplateView

from ..decorators import group_required
from ..forms import UserCreateForm, UserUpdateForm
from ..models import KYCProfile, KYCDocument


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class AdminDashboardView(TemplateView):
    """Display admin dashboard with KYC statistics."""
    template_name = "kyc/admin/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profiles = KYCProfile.objects.all().order_by('-created_at')

        context['profiles'] = profiles
        context['total_profiles'] = profiles.count()
        context['pending_count'] = profiles.filter(status='Pending').count()
        context['approved_count'] = profiles.filter(status='Approved').count()
        context['rejected_count'] = profiles.filter(status='Rejected').count()
        context['under_review_count'] = profiles.filter(status='Under Review').count()

        return context


@login_required
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
            else:
                messages.error(request, 'Please correct the errors in the create form.')

        elif action == 'update':
            user_id = request.POST.get('user_id')
            edit_user = get_object_or_404(User, pk=user_id)
            edit_form = UserUpdateForm(request.POST, instance=edit_user)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'User updated successfully.')
                return redirect('user_management')
            else:
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

    return render(request, 'kyc/admin/user_management.html', {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'super_users': super_users,
        'create_form': create_form,
        'edit_user': edit_user,
        'edit_form': edit_form,
    })


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class DocumentReviewView(View):
    """Review and approve/reject KYC profiles."""

    def get(self, request, pk, *args, **kwargs):
        profile = get_object_or_404(KYCProfile, pk=pk)
        documents = profile.documents.all().order_by('-uploaded_at')
        first_document = documents.first()

        return render(request, 'kyc/admin/document_review.html', {
            'profile': profile,
            'documents': documents,
            'first_document': first_document,
        })

    def post(self, request, pk, *args, **kwargs):
        profile = get_object_or_404(KYCProfile, pk=pk)
        documents = profile.documents.all().order_by('-uploaded_at')

        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '')

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


@method_decorator([login_required], name='dispatch')
class DocumentDetailView(View):
    """View document details with permission checks."""

    def get(self, request, pk, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name__in=['verifier', 'admin']).exists():
            document = get_object_or_404(KYCDocument, pk=pk)
        elif request.user.groups.filter(name='client').exists():
            document = get_object_or_404(
                KYCDocument,
                pk=pk,
                profile__user=request.user
            )
        else:
            raise PermissionDenied

        return render(request, 'kyc/admin/document_detail.html', {
            'document': document
        })


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class BulkUpdateStatusView(View):
    """Bulk update status for multiple KYC profiles."""

    def post(self, request, *args, **kwargs):
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


# Export views for URL compatibility
admin_dashboard = AdminDashboardView.as_view()
user_management = user_management
document_review = DocumentReviewView.as_view()
document_detail = DocumentDetailView.as_view()
bulk_update_status = BulkUpdateStatusView.as_view()
