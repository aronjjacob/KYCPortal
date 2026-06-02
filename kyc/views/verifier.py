from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Avg, ExpressionWrapper, F, DurationField

from ..decorators import group_required
from ..models import KYCApplication

PAGE_SIZE = 10


def _build_page_numbers(current_page, total_pages):
    if total_pages <= 7:
        return list(range(1, total_pages + 1))

    pages = [1]
    if current_page > 4:
        pages.append("...")

    start = max(2, current_page - 1)
    end = min(total_pages - 1, current_page + 1)

    for page in range(start, end + 1):
        if page not in pages:
            pages.append(page)

    if current_page < total_pages - 3:
        pages.append("...")

    if total_pages not in pages:
        pages.append(total_pages)

    return pages


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class VerifierDashboardView(TemplateView):
    template_name = "kyc/verifier/verifier_dashboard.html"
    paginate_by = 10

    def _build_page_numbers(self, current_page, total_pages):
        if total_pages <= 7:
            return list(range(1, total_pages + 1))

        pages = [1]
        if current_page > 4:
            pages.append("...")

        start = max(2, current_page - 1)
        end = min(total_pages - 1, current_page + 1)

        for page in range(start, end + 1):
            if page not in pages:
                pages.append(page)

        if current_page < total_pages - 3:
            pages.append("...")

        if total_pages not in pages:
            pages.append(total_pages)

        return pages

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applications = KYCApplication.objects.select_related("profile", "user", "document").order_by("-created_at")
        paginator = Paginator(applications, self.paginate_by)
        page_number = self.request.GET.get("page", 1)

        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)

        today = timezone.localdate()
        completed_today = applications.filter(status="approved", updated_at__date=today).count()
        pending_review = applications.filter(status__in=["pending", "under_review"]).count()
        total_count = applications.count()
        goal = 25
        completion_percent = int(min(100, (completed_today / goal) * 100)) if goal else 0

        context.update(
            {
                "page_obj": page_obj,
                "applications": page_obj.object_list,
                "total_assigned": total_count,
                "pending_review_count": pending_review,
                "completed_today_count": completed_today,
                "completed_today_goal": goal,
                "completed_today_pct": completion_percent,
                "page_numbers": _build_page_numbers(page_obj.number, paginator.num_pages),
            }
        )
        return context


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
class VerifierDocumentReviewView(TemplateView):
    template_name = "kyc/verifier/document_review.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = get_object_or_404(
            KYCApplication.objects.select_related("profile", "user", "document"),
            pk=kwargs.get("pk"),
        )
        profile = application.profile
        documents = profile.documents.all().order_by("-uploaded_at")
        first_document = documents.first()

        context.update(
            {
                "application": application,
                "profile": profile,
                "documents": documents,
                "first_document": first_document,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        application = get_object_or_404(
            KYCApplication.objects.select_related("profile", "document"),
            pk=kwargs.get("pk"),
        )
        profile = application.profile
        action = request.POST.get("action")
        remarks = request.POST.get("remarks", "").strip()

        if action == "approve":
            application.status = "approved"
            profile.status = "Approved"
        elif action == "reject":
            application.status = "rejected"
            profile.status = "Rejected"
        elif action == "under_review":
            application.status = "under_review"
            profile.status = "Under Review"
        elif action == "request_resubmission":
            application.status = "pending"
            profile.status = "Resubmission Required"
        else:
            messages.error(request, "Invalid review action.")
            return redirect("verifier_document_review", pk=application.pk)

        application.save()
        profile.save()

        if application.document and remarks:
            application.document.remarks = remarks
            application.document.save()

        messages.success(request, "KYC application review was saved successfully.")
        return redirect("verifier_review_queue")


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class VerifierVerificationHistoryView(TemplateView):
    template_name = "kyc/verifier/verification_history.html"
    paginate_by = PAGE_SIZE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        processed_apps = KYCApplication.objects.select_related("profile", "user", "document").filter(
            status__in=["approved", "rejected"]
        ).order_by("-updated_at")
        paginator = Paginator(processed_apps, self.paginate_by)
        page_number = self.request.GET.get("page", 1)

        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)

        total_processed = processed_apps.count()
        approved_count = processed_apps.filter(status="approved").count()
        approval_rate = int((approved_count / total_processed) * 100) if total_processed else 0

        avg_review_duration = processed_apps.aggregate(
            avg_time=Avg(
                ExpressionWrapper(
                    F("updated_at") - F("created_at"),
                    output_field=DurationField(),
                )
            )
        )["avg_time"]
        average_minutes = int(avg_review_duration.total_seconds() / 60) if avg_review_duration else 0

        context.update(
            {
                "page_obj": page_obj,
                "applications": page_obj.object_list,
                "page_numbers": _build_page_numbers(page_obj.number, paginator.num_pages),
                "total_processed": total_processed,
                "approval_rate": approval_rate,
                "avg_review_minutes": average_minutes,
            }
        )
        return context


# keep same view names for URL imports
verifier_dashboard = VerifierDashboardView.as_view()
verifier_review_queue = VerifierReviewQueueView.as_view()
verifier_document_review = VerifierDocumentReviewView.as_view()
verifier_verification_history = VerifierVerificationHistoryView.as_view()
