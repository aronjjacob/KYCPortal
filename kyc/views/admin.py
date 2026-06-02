from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from datetime import timedelta

from ..decorators import group_required
from ..forms import UserCreateForm, UserUpdateForm
from ..models import KYCProfile, KYCDocument, KYCApplication, AdminDashboardFeature, AuditLog
from .verifier import _build_page_numbers

PAGE_SIZE = 10

@method_decorator([login_required, group_required('verifier')], name='dispatch')
class AdminDashboardView(TemplateView):
    """Display admin dashboard with KYC statistics."""
    template_name = "kyc/admin/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profiles = KYCProfile.objects.all().order_by('-created_at')
        
        # Get actual statistics
        context['profiles'] = profiles
        context['total_profiles'] = profiles.count()
        context['pending_count'] = profiles.filter(status='Pending').count()
        context['approved_count'] = profiles.filter(status='Approved').count()
        context['rejected_count'] = profiles.filter(status='Rejected').count()
        context['under_review_count'] = profiles.filter(status='Under Review').count()
        
        # Get today's approved count
        today = timezone.now().date()
        context['approved_today'] = profiles.filter(
            status='Approved',
            created_at__date=today
        ).count()
        
        # Get total users
        User = get_user_model()
        context['total_users'] = User.objects.count()
        
        # Get active features for quick actions
        context['features'] = AdminDashboardFeature.objects.filter(is_active=True)

        # Application-level stats
        applications = KYCApplication.objects.select_related('profile', 'user').order_by('-created_at')
        context['total_assigned'] = applications.count()
        context['pending_review_count'] = applications.filter(status__in=['pending', 'under_review']).count()

        # Completed today (applications approved today)
        completed_today = applications.filter(status='approved', updated_at__date=today).count()
        context['completed_today_count'] = completed_today
        goal = 25
        context['completed_today_goal'] = goal
        context['completed_today_pct'] = int(min(100, (completed_today / goal) * 100)) if goal else 0

        # Approval rate and avg review time (processed apps)
        processed = KYCApplication.objects.filter(status__in=['approved', 'rejected'])
        total_processed = processed.count()
        approved_count = processed.filter(status='approved').count()
        context['total_processed'] = total_processed
        context['approval_rate'] = int((approved_count / total_processed) * 100) if total_processed else 0

        from django.db.models import Avg, ExpressionWrapper, F, DurationField
        avg_review_duration = processed.aggregate(
            avg_time=Avg(
                ExpressionWrapper(
                    F('updated_at') - F('created_at'),
                    output_field=DurationField(),
                )
            )
        )['avg_time']
        context['avg_review_minutes'] = int(avg_review_duration.total_seconds() / 60) if avg_review_duration else 0

        # Recent activity
        context['recent_audits'] = AuditLog.objects.select_related('verifier', 'application').order_by('-timestamp')[:6]
        context['recent_applications'] = applications.order_by('-updated_at')[:6]
        
        return context


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class UserManagementView(View):
    """Manage users: create, update, delete with group assignments."""

    def get(self, request, *args, **kwargs):
        User = get_user_model()
        users_list = User.objects.all().prefetch_related('groups').order_by('username')
        
        # Paginate users (10 per page)
        paginator = Paginator(users_list, 10)
        page_number = request.GET.get('page', 1)
        try:
            users = paginator.page(page_number)
        except:
            users = paginator.page(1)
        
        edit_user = None
        edit_form = None
        create_form = UserCreateForm()
        
        edit_id = request.GET.get('edit')
        if edit_id:
            edit_user = get_object_or_404(User, pk=edit_id)
            edit_form = UserUpdateForm(instance=edit_user)
        
        total_users = users_list.count()
        active_users = users_list.filter(is_active=True).count()
        staff_users = users_list.filter(is_staff=True).count()
        super_users = users_list.filter(is_superuser=True).count()
        
        return render(request, 'kyc/admin/user_management.html', {
            'users': users,
            'paginator': paginator,
            'page_obj': users,
            'total_users': total_users,
            'active_users': active_users,
            'staff_users': staff_users,
            'super_users': super_users,
            'create_form': create_form,
            'edit_user': edit_user,
            'edit_form': edit_form,
        })

    def post(self, request, *args, **kwargs):
        User = get_user_model()
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

        # Map actions to both Profile and Application statuses
        status_map = {
            'approve': ('Approved', 'approved'),
            'reject': ('Rejected', 'rejected'),
            'under_review': ('Under Review', 'under_review'),
            'resubmission': ('Resubmission Required', 'pending'),
        }

        if action not in status_map:
            messages.error(request, 'Invalid action.')
            return redirect('document_review', pk=profile.pk)

        profile_status, app_status = status_map[action]
        profile.status = profile_status
        profile.save()

        if hasattr(profile, 'application'):
            profile.application.status = app_status
            profile.application.save()

        # create audit log entry for this admin review action
        try:
            verifier_name = request.user.get_full_name() or request.user.username
        except Exception:
            verifier_name = 'Unknown'

        AuditLog.objects.create(
            application=getattr(profile, 'application', None),
            verifier=request.user if request.user.is_authenticated else None,
            verifier_name=verifier_name,
            action=app_status,
            remarks=remarks,
        )

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

        app_status_map = {
            'Approved': 'approved',
            'Rejected': 'rejected',
            'Under Review': 'under_review',
            'Resubmission Required': 'pending'
        }

        if selected_profiles and new_status in allowed_statuses:
            KYCProfile.objects.filter(id__in=selected_profiles).update(status=new_status)
            KYCApplication.objects.filter(profile_id__in=selected_profiles).update(status=app_status_map[new_status])
            messages.success(request, 'Selected KYC records have been updated.')
        else:
            messages.error(request, 'Please select records and a valid status.')

        return redirect('admin_dashboard')

@method_decorator([login_required, group_required('verifier')], name='dispatch')
class VerifierReviewQueueView(TemplateView):
    template_name = "kyc/verifier/review_queue.html"
    paginate_by = PAGE_SIZE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applications = KYCApplication.objects.select_related("profile", "user", "document").filter(
            status__in=["pending", "under_review"]
        ).order_by("-created_at")
        paginator = Paginator(applications, self.paginate_by)
        page_number = self.request.GET.get("page", 1)

        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)

        context.update(
            {
                "page_obj": page_obj,
                "applications": page_obj.object_list,
                "page_numbers": _build_page_numbers(page_obj.number, paginator.num_pages),
                "total_applications": applications.count(),
            }
        )
        return context


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class AuditLogView(TemplateView):
    template_name = "kyc/admin/audit_log.html"
    paginate_by = PAGE_SIZE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Base queryset
        logs = AuditLog.objects.select_related('verifier', 'application', 'application__user').order_by('-timestamp')

        # Filters from query params
        q = self.request.GET.get('q', '').strip()
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        event_type = self.request.GET.get('event_type', '').strip()

        from django.db.models import Q
        if q:
            # search verifier name, username, action, or application id
            filters = Q(verifier_name__icontains=q) | Q(verifier__username__icontains=q) | Q(action__icontains=q)
            if q.isdigit():
                filters |= Q(application__id=int(q))
            logs = logs.filter(filters)

        if event_type:
            logs = logs.filter(action__iexact=event_type)

        if start_date:
            try:
                from django.utils.dateparse import parse_date

                sd = parse_date(start_date)
                if sd:
                    logs = logs.filter(timestamp__date__gte=sd)
            except Exception:
                pass

        if end_date:
            try:
                from django.utils.dateparse import parse_date

                ed = parse_date(end_date)
                if ed:
                    logs = logs.filter(timestamp__date__lte=ed)
            except Exception:
                pass

        # Export CSV if requested
        if self.request.GET.get('export') == 'csv':
            import csv
            from django.http import HttpResponse

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="audit_log.csv"'

            writer = csv.writer(response)
            writer.writerow(['timestamp', 'verifier_name', 'verifier_username', 'application_id', 'action', 'remarks'])
            for l in logs:
                writer.writerow([
                    l.timestamp.isoformat(),
                    l.verifier_name,
                    l.verifier.username if l.verifier else '',
                    l.application.id if l.application else '',
                    l.action,
                    (l.remarks or ''),
                ])
            return response

        # pagination
        paginator = Paginator(logs, self.paginate_by)
        page_number = self.request.GET.get('page', 1)

        try:
            page_obj = paginator.page(page_number)
        except Exception:
            page_obj = paginator.page(1)

        # build base querystring excluding page for pagination links and export link
        params = self.request.GET.copy()
        if 'page' in params:
            params.pop('page')
        base_qs = params.urlencode()

        # Only show approved and rejected in the dropdown
        event_types = ['approved', 'rejected']

        context.update({
            'page_obj': page_obj,
            'audit_logs': page_obj.object_list,
            'page_numbers': _build_page_numbers(page_obj.number, paginator.num_pages),
            'total_logs': logs.count(),
            'base_qs': base_qs,
            'event_types': event_types,
            'current_q': q,
            'current_start_date': start_date,
            'current_end_date': end_date,
            'current_event_type': event_type,
        })

        return context



# Export as_view() with original names for URL compatibility
admin_dashboard = AdminDashboardView.as_view()
user_management = UserManagementView.as_view()
document_review = DocumentReviewView.as_view()
document_detail = DocumentDetailView.as_view()
bulk_update_status = BulkUpdateStatusView.as_view()
audit_log = AuditLogView.as_view()
