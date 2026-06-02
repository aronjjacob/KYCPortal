from .client import kyc_upload, kyc_documents, kyc_liveness, kyc_finalize, kyc_status, client_dashboard
from .admin import (
    admin_dashboard,
    document_review,
    user_management,
    document_detail,
    bulk_update_status,
    audit_log
)
from .verifier import (
    verifier_dashboard,
    verifier_review_queue,
    verifier_document_review,
    verifier_verification_history,
)

__all__ = [
    # Client views
    "kyc_upload",
    "kyc_documents",
    "kyc_liveness",
    "kyc_finalize",
    "kyc_status",
    "client_dashboard",
    # Admin views
    "admin_dashboard",
    "document_review",
    "user_management",
    "document_detail",
    "bulk_update_status",
    # Verifier views
    "verifier_dashboard",
    "verifier_review_queue",
    "verifier_document_review",
    "verifier_verification_history",
]
