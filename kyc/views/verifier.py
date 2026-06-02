from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from ..decorators import group_required


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class VerifierDashboardView(TemplateView):
    template_name = "kyc/verifier/verifier_dashboard.html"


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class VerifierReviewQueueView(TemplateView):
    template_name = "kyc/verifier/review_queue.html"


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class VerifierDocumentReviewView(TemplateView):
    template_name = "kyc/verifier/document_review.html"


@method_decorator([login_required, group_required('verifier')], name='dispatch')
class VerifierVerificationHistoryView(TemplateView):
    template_name = "kyc/verifier/verification_history.html"


# keep same view names for URL imports
verifier_dashboard = VerifierDashboardView.as_view()
verifier_review_queue = VerifierReviewQueueView.as_view()
verifier_document_review = VerifierDocumentReviewView.as_view()
verifier_verification_history = VerifierVerificationHistoryView.as_view()
