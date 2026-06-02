from django import forms
from .models import KYCProfile, KYCDocument


class KYCProfileForm(forms.ModelForm):
    class Meta:
        model = KYCProfile
        fields = ['full_name', 'date_of_birth', 'address']


class KYCDocumentForm(forms.ModelForm):
    class Meta:
        model = KYCDocument
        fields = ['document_type', 'front_image', 'back_image', 'selfie_image']