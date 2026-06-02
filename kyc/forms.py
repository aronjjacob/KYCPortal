from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

from .models import KYCProfile, KYCDocument


class KYCProfileForm(forms.ModelForm):
    class Meta:
        model = KYCProfile
        fields = ['full_name', 'date_of_birth', 'address']


class KYCDocumentForm(forms.ModelForm):
    class Meta:
        model = KYCDocument
        fields = ['document_type', 'front_image', 'back_image', 'selfie_image']


class UserCreateForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    email = forms.EmailField(required=False)
    is_active = forms.BooleanField(required=False, initial=True)
    is_staff = forms.BooleanField(required=False)
    is_superuser = forms.BooleanField(required=False)
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'size': 4})
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'groups')


class UserUpdateForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'size': 4})
    )

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'is_active', 'is_staff', 'is_superuser', 'groups')