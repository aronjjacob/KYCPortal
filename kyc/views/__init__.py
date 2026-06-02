from .client import kyc_upload, kyc_documents, kyc_liveness, kyc_finalize, client_dashboard
from .admin import admin_dashboard, document_review
from .verifier import (
    verifier_dashboard,
    verifier_review_queue,
    verifier_document_review,
    verifier_verification_history,
)

__all__ = [
    "kyc_upload",
    "kyc_documents",
    "kyc_liveness",
    "kyc_finalize",
    "client_dashboard",
    "admin_dashboard",
    "document_review",
    "verifier_dashboard",
    "verifier_review_queue",
    "verifier_document_review",
    "verifier_verification_history",
]
