from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
    path('upload/', views.kyc_upload, name='kyc_upload'),
    path('documents/', views.kyc_documents, name='kyc_documents'),
    path('liveness/', views.kyc_liveness, name='kyc_liveness'),
    path('finalize/', views.kyc_finalize, name='kyc_finalize'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user-management/', views.user_management, name='user_management'),
    path('review/', views.document_review, name='document_review'),
]