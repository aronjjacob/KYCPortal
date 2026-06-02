from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import TemplateView

from ..forms import KYCProfileForm, KYCDocumentForm
from ..decorators import group_required


@method_decorator([login_required, group_required('client')], name='dispatch')
class KYCUploadView(View):
    def get(self, request, *args, **kwargs):
        profile_form = KYCProfileForm()
        document_form = KYCDocumentForm()
        return render(request, "kyc/client/kyc_upload.html", {"profile_form": profile_form, "document_form": document_form})

    def post(self, request, *args, **kwargs):
        profile_form = KYCProfileForm(request.POST)
        document_form = KYCDocumentForm(request.POST, request.FILES)

        if profile_form.is_valid() and document_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()

            document = document_form.save(commit=False)
            document.profile = profile
            document.save()

            return redirect("client_dashboard")

        return render(request, "kyc/client/kyc_upload.html", {"profile_form": profile_form, "document_form": document_form})


@method_decorator([login_required, group_required('client')], name='dispatch')
class KYCDocumentsView(TemplateView):
    template_name = "kyc/client/kyc_documents.html"


@method_decorator([login_required, group_required('client')], name='dispatch')
class KYCLivenessView(TemplateView):
    template_name = "kyc/client/kyc_liveness.html"


@method_decorator([login_required, group_required('client')], name='dispatch')
class KYCFinalizeView(TemplateView):
    template_name = "kyc/client/kyc_finalize.html"


@method_decorator([login_required, group_required('client')], name='dispatch')
class ClientDashboardView(TemplateView):
    template_name = "kyc/client/client_dashboard.html"


# keep same view names for URL imports
kyc_upload = KYCUploadView.as_view()
kyc_documents = KYCDocumentsView.as_view()
kyc_liveness = KYCLivenessView.as_view()
kyc_finalize = KYCFinalizeView.as_view()
client_dashboard = ClientDashboardView.as_view()
