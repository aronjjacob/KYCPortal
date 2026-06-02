from django.urls import path
from . import views

urlpatterns = [
   # Client URLs
   
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
    path('upload/', views.kyc_upload, name='kyc_upload'),
    path('documents/', views.kyc_documents, name='kyc_documents'),
    path('liveness/', views.kyc_liveness, name='kyc_liveness'),
    path('finalize/', views.kyc_finalize, name='kyc_finalize'),
   
   # Verifier URLs
   
    path('verifier-dashboard/', views.verifier_dashboard, name='verifier_dashboard'),
    path('verifier-review-queue/', views.verifier_review_queue, name='verifier_review_queue'),
    path('verifier-document-review/', views.verifier_document_review, name='verifier_document_review'),
    path('verifier-verification-history/', views.verifier_verification_history, name='verifier_verification_history'),







    # Admin URLs

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('review/', views.document_review, name='document_review'),
]