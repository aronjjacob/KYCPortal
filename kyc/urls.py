from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
    path('upload/', views.kyc_upload, name='kyc_upload'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('review/', views.document_review, name='document_review'),
]