import os
import uuid
from datetime import datetime
from types import SimpleNamespace

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db import OperationalError
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView

from ..decorators import group_required
from ..forms import KYCProfileForm, KYCDocumentForm, KYCLivenessForm, KYCFinalizeForm
from ..models import KYCApplication, KYCProfile, KYCDocument


def _get_profile(user):
    return KYCProfile.objects.filter(user=user).first()


def _get_session_personal_info(request):
    return request.session.get('personal_info', {})


def _get_session_document_info(request):
    return request.session.get('document_info', {})


def _get_session_liveness_info(request):
    return request.session.get('liveness_info', {})


def _parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    return value


def _build_file_reference(path):
    if not path:
        return None
    try:
        return SimpleNamespace(url=default_storage.url(path), name=os.path.basename(path))
    except Exception:
        return None


def _build_session_document(document_info, liveness_info=None):
    return SimpleNamespace(
        document_type=document_info.get('document_type'),
        id_number=document_info.get('id_number'),
        front_image=_build_file_reference(document_info.get('front_id')),
        back_image=_build_file_reference(document_info.get('back_id')),
        selfie_image=_build_file_reference((liveness_info or {}).get('selfie')),
    )


def _build_session_profile(personal_info):
    data = personal_info.copy()
    data['date_of_birth'] = _parse_date(data.get('date_of_birth'))
    data['address'] = data.get('address') or ', '.join(
        part for part in (
            data.get('street_address', ''),
            data.get('city', ''),
            data.get('postal_code', ''),
            data.get('country', ''),
        )
        if part
    )
    data['get_gender_display'] = dict(KYCProfile.GENDER_CHOICES).get(data.get('gender', ''), '')
    return SimpleNamespace(**data)


def _save_uploaded_file(uploaded_file, folder):
    extension = os.path.splitext(uploaded_file.name)[1]
    name = f"{uuid.uuid4().hex}{extension}"
    path = os.path.join(folder, name).replace('\\', '/')
    return default_storage.save(path, uploaded_file)


def _delete_stored_file(path):
    if path and default_storage.exists(path):
        default_storage.delete(path)


def _personal_info_required(request):
    personal_info = _get_session_personal_info(request)
    return bool(personal_info.get('full_name') and personal_info.get('date_of_birth'))


def _document_info_complete(document_info):
    return bool(
        document_info.get('document_type')
        and document_info.get('front_id')
        and document_info.get('back_id')
    )


def _liveness_info_complete(liveness_info):
    return bool(liveness_info.get('selfie'))


def verify_document(application):
    # Placeholder for a real document verification integration.
    return True


def verify_selfie(application):
    # Placeholder for a real selfie verification integration.
    return True


@method_decorator([login_required, group_required('client')], name='dispatch')
class KYCUploadView(View):
    def get(self, request, *args, **kwargs):
        existing_profile = _get_profile(request.user)
        personal_info = _get_session_personal_info(request)
        profile_form = KYCProfileForm(initial=personal_info, instance=existing_profile)

        return render(
            request,
            'kyc/client/kyc_upload.html',
            {'profile_form': profile_form, 'profile': existing_profile},
        )

    def post(self, request, *args, **kwargs):
        profile_form = KYCProfileForm(request.POST)
        if profile_form.is_valid():
            cleaned = profile_form.cleaned_data
            contact_number = ''.join([
                cleaned.get('phone_country_code', ''),
                ' ' if cleaned.get('phone_country_code') and cleaned.get('phone_number') else '',
                cleaned.get('phone_number', ''),
            ]).strip()
            address = ', '.join(
                part for part in (
                    cleaned.get('street_address', ''),
                    cleaned.get('city', ''),
                    cleaned.get('postal_code', ''),
                    cleaned.get('country', ''),
                )
                if part
            )
            request.session['personal_info'] = {
                'full_name': cleaned.get('full_name', ''),
                'date_of_birth': cleaned.get('date_of_birth').isoformat() if cleaned.get('date_of_birth') else '',
                'gender': cleaned.get('gender', ''),
                'email': cleaned.get('email', ''),
                'contact_number': contact_number,
                'phone_country_code': cleaned.get('phone_country_code', ''),
                'phone_number': cleaned.get('phone_number', ''),
                'street_address': cleaned.get('street_address', ''),
                'city': cleaned.get('city', ''),
                'postal_code': cleaned.get('postal_code', ''),
                'country': cleaned.get('country', ''),
                'address': address,
            }
            request.session.modified = True
            return redirect('kyc_documents')

        messages.error(request, 'Please check your details and try again.')
        return render(request, 'kyc/client/kyc_upload.html', {'profile_form': profile_form})


@method_decorator([login_required, group_required('client')], name='dispatch')
class KYCDocumentsView(View):
    def get(self, request, *args, **kwargs):
        if not _personal_info_required(request):
            messages.warning(request, 'Please complete your personal information first.')
            return redirect('kyc_upload')

        document_info = _get_session_document_info(request)
        liveness_info = _get_session_liveness_info(request)
        document = _build_session_document(document_info, liveness_info)
        document_form = KYCDocumentForm(
            initial={
                'document_type': document_info.get('document_type', ''),
                'id_number': document_info.get('id_number', ''),
            },
            existing_files={
                'front_image': document_info.get('front_id'),
                'back_image': document_info.get('back_id'),
            },
        )

        return render(
            request,
            'kyc/client/kyc_documents.html',
            {
                'document': document,
                'document_form': document_form,
                'document_types': KYCDocument.DOCUMENT_TYPES,
            },
        )

    def post(self, request, *args, **kwargs):
        if not _personal_info_required(request):
            messages.warning(request, 'Please complete your personal information first.')
            return redirect('kyc_upload')

        document_info = _get_session_document_info(request)
        existing_files = {
            'front_image': document_info.get('front_id'),
            'back_image': document_info.get('back_id'),
        }
        document_form = KYCDocumentForm(
            request.POST,
            request.FILES,
            existing_files=existing_files,
        )

        if document_form.is_valid():
            cleaned = document_form.cleaned_data
            front_path = document_info.get('front_id')
            back_path = document_info.get('back_id')

            front_upload = request.FILES.get('front_image')
            if front_upload:
                _delete_stored_file(front_path)
                front_path = _save_uploaded_file(front_upload, 'kyc/temp/front_ids')

            back_upload = request.FILES.get('back_image')
            if back_upload:
                _delete_stored_file(back_path)
                back_path = _save_uploaded_file(back_upload, 'kyc/temp/back_ids')

            request.session['document_info'] = {
                'document_type': cleaned.get('document_type', ''),
                'id_number': cleaned.get('id_number', ''),
                'front_id': front_path,
                'back_id': back_path,
            }
            request.session.modified = True
            messages.success(request, 'Document information saved to session.')
            return redirect('kyc_liveness')

        document = _build_session_document(document_info, _get_session_liveness_info(request))
        messages.error(request, 'Please check the document fields and try again.')
        return render(
            request,
            'kyc/client/kyc_documents.html',
            {
                'document': document,
                'document_form': document_form,
                'document_types': KYCDocument.DOCUMENT_TYPES,
            },
        )


@method_decorator([login_required, group_required('client')], name='dispatch')
class KYCLivenessView(View):
    def get(self, request, *args, **kwargs):
        if not _personal_info_required(request):
            messages.warning(request, 'Please complete your personal information first.')
            return redirect('kyc_upload')

        document_info = _get_session_document_info(request)
        if not _document_info_complete(document_info):
            messages.warning(request, 'Please upload the front and back of your identification document first.')
            return redirect('kyc_documents')

        liveness_info = _get_session_liveness_info(request)
        document = _build_session_document(document_info, liveness_info)
        liveness_form = KYCLivenessForm(existing_selfie=liveness_info.get('selfie'))

        return render(
            request,
            'kyc/client/kyc_liveness.html',
            {
                'document': document,
                'liveness_form': liveness_form,
            },
        )

    def post(self, request, *args, **kwargs):
        if not _personal_info_required(request):
            messages.warning(request, 'Please complete your personal information first.')
            return redirect('kyc_upload')

        document_info = _get_session_document_info(request)
        if not _document_info_complete(document_info):
            messages.warning(request, 'Please upload the front and back of your identification document first.')
            return redirect('kyc_documents')

        liveness_info = _get_session_liveness_info(request)
        liveness_form = KYCLivenessForm(
            request.POST,
            request.FILES,
            existing_selfie=liveness_info.get('selfie'),
        )

        if liveness_form.is_valid():
            selfie_path = liveness_info.get('selfie')
            selfie_upload = request.FILES.get('selfie_image')
            if selfie_upload:
                _delete_stored_file(selfie_path)
                selfie_path = _save_uploaded_file(selfie_upload, 'kyc/temp/selfies')

            request.session['liveness_info'] = {'selfie': selfie_path}
            request.session.modified = True
            messages.success(request, 'Selfie saved to session.')
            return redirect('kyc_finalize')

        document = _build_session_document(document_info, liveness_info)
        messages.error(request, 'Please upload a valid liveness photo.')
        return render(
            request,
            'kyc/client/kyc_liveness.html',
            {
                'document': document,
                'liveness_form': liveness_form,
            },
        )


@method_decorator([login_required, group_required('client')], name='dispatch')
class KYCFinalizeView(View):
    def get(self, request, *args, **kwargs):
        personal_info = _get_session_personal_info(request)
        document_info = _get_session_document_info(request)
        liveness_info = _get_session_liveness_info(request)

        if not _personal_info_required(request):
            messages.warning(request, 'Please complete your personal information first.')
            return redirect('kyc_upload')
        if not _document_info_complete(document_info):
            messages.warning(request, 'Please upload the front and back of your identification document first.')
            return redirect('kyc_documents')
        if not _liveness_info_complete(liveness_info):
            messages.warning(request, 'Please complete the liveness check first.')
            return redirect('kyc_liveness')

        profile = _build_session_profile(personal_info)
        document = _build_session_document(document_info, liveness_info)
        finalize_form = KYCFinalizeForm()

        return render(
            request,
            'kyc/client/kyc_finalize.html',
            {
                'profile': profile,
                'document': document,
                'finalize_form': finalize_form,
            },
        )

    def post(self, request, *args, **kwargs):
        personal_info = _get_session_personal_info(request)
        document_info = _get_session_document_info(request)
        liveness_info = _get_session_liveness_info(request)

        if not _personal_info_required(request):
            messages.warning(request, 'Please complete your personal information first.')
            return redirect('kyc_upload')
        if not _document_info_complete(document_info):
            messages.warning(request, 'Please upload the front and back of your identification document first.')
            return redirect('kyc_documents')
        if not _liveness_info_complete(liveness_info):
            messages.warning(request, 'Please complete the liveness check first.')
            return redirect('kyc_liveness')

        finalize_form = KYCFinalizeForm(request.POST)
        if finalize_form.is_valid():
            profile, _ = KYCProfile.objects.update_or_create(
                user=request.user,
                defaults={
                    'full_name': personal_info.get('full_name', ''),
                    'date_of_birth': _parse_date(personal_info.get('date_of_birth')),
                    'gender': personal_info.get('gender', ''),
                    'email': personal_info.get('email', ''),
                    'phone_number': personal_info.get('contact_number', ''),
                    'street_address': personal_info.get('street_address', ''),
                    'city': personal_info.get('city', ''),
                    'postal_code': personal_info.get('postal_code', ''),
                    'country': personal_info.get('country', ''),
                    'address': personal_info.get('address', ''),
                    'status': 'Pending',
                },
            )

            document = KYCDocument.objects.create(
                profile=profile,
                document_type=document_info.get('document_type', ''),
                id_number=document_info.get('id_number', ''),
            )
            if document_info.get('front_id'):
                document.front_image.name = document_info.get('front_id')
            if document_info.get('back_id'):
                document.back_image.name = document_info.get('back_id')
            if liveness_info.get('selfie'):
                document.selfie_image.name = liveness_info.get('selfie')
            document.save()

            try:
                application = KYCApplication.objects.create(
                    user=request.user,
                    profile=profile,
                    document=document,
                    status='pending',
                )
                verify_document(application)
                verify_selfie(application)
            except OperationalError:
                application = None

            profile.status = 'Under Review'
            profile.save()

            request.session.pop('personal_info', None)
            request.session.pop('document_info', None)
            request.session.pop('liveness_info', None)
            request.session.modified = True

            messages.success(request, 'Your application has been submitted for review.')
            return redirect('client_dashboard')

        messages.error(request, 'Please confirm all declarations before submitting.')
        profile = _build_session_profile(personal_info)
        document = _build_session_document(document_info, liveness_info)
        return render(
            request,
            'kyc/client/kyc_finalize.html',
            {
                'profile': profile,
                'document': document,
                'finalize_form': finalize_form,
            },
        )


@method_decorator([login_required, group_required('client')], name='dispatch')
class KYCStatusView(View):
    def get(self, request, *args, **kwargs):
        application = KYCApplication.objects.filter(user=request.user).order_by('-created_at').first()
        profile = application.profile if application else _get_profile(request.user)
        document = application.document if application else None

        return render(
            request,
            'kyc/client/kyc_status.html',
            {'profile': profile, 'document': document, 'application': application},
        )


@method_decorator([login_required, group_required('client')], name='dispatch')
class ClientDashboardView(TemplateView):
    template_name = 'kyc/client/client_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = _get_profile(self.request.user)
        return context


kyc_upload = KYCUploadView.as_view()
kyc_documents = KYCDocumentsView.as_view()
kyc_liveness = KYCLivenessView.as_view()
kyc_finalize = KYCFinalizeView.as_view()
kyc_status = KYCStatusView.as_view()
client_dashboard = ClientDashboardView.as_view()
