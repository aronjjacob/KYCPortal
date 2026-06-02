from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

from .models import KYCProfile, KYCDocument


class KYCProfileForm(forms.ModelForm):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    PHONE_COUNTRY_CHOICES = [
        ('+1', '+1 US'),
        ('+44', '+44 UK'),
        ('+91', '+91 IN'),
        ('+61', '+61 AU'),
    ]

    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=True)
    phone_country_code = forms.ChoiceField(choices=PHONE_COUNTRY_CHOICES, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=True)
    street_address = forms.CharField(required=True)
    city = forms.CharField(required=True)
    postal_code = forms.CharField(required=True)
    country = forms.CharField(required=True)

    class Meta:
        model = KYCProfile
        fields = [
            'full_name',
            'date_of_birth',
            'gender',
            'email',
            'phone_number',
            'street_address',
            'city',
            'postal_code',
            'country',
            'address',
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        if instance and instance.phone_number:
            parts = instance.phone_number.split(' ', 1)
            if len(parts) > 1:
                self.fields['phone_country_code'].initial = parts[0]
                self.fields['phone_number'].initial = parts[1]
            else:
                self.fields['phone_number'].initial = instance.phone_number

    def save(self, commit=True):
        profile = super().save(commit=False)
        country_code = self.cleaned_data.get('phone_country_code', '')
        phone_number = self.cleaned_data.get('phone_number', '')
        if country_code and phone_number:
            profile.phone_number = f'{country_code} {phone_number}'
        else:
            profile.phone_number = phone_number

        address_parts = [
            self.cleaned_data.get('street_address', ''),
            self.cleaned_data.get('city', ''),
            self.cleaned_data.get('postal_code', ''),
            self.cleaned_data.get('country', ''),
        ]
        profile.address = ', '.join([part for part in address_parts if part])

        if commit:
            profile.save()
        return profile


DOCUMENT_FILE_INPUT_CLASS = (
    'block w-full text-body-sm text-on-surface '
    'file:mr-4 file:py-2.5 file:px-6 file:rounded-lg file:border-0 '
    'file:bg-primary file:text-white file:font-label-md '
    'hover:file:bg-primary-container file:cursor-pointer'
)


class KYCDocumentForm(forms.ModelForm):
    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/jpg', 'image/png'}

    def __init__(self, *args, existing_files=None, **kwargs):
        self.existing_files = existing_files or {}
        super().__init__(*args, **kwargs)
        self.fields['document_type'].choices = [
            ('', 'Select document type'),
            *KYCDocument.DOCUMENT_TYPES,
        ]

    class Meta:
        model = KYCDocument
        fields = ['document_type', 'id_number', 'front_image', 'back_image']
        widgets = {
            'front_image': forms.FileInput(
                attrs={
                    'accept': 'image/jpeg,image/png,.jpg,.jpeg,.png',
                    'class': DOCUMENT_FILE_INPUT_CLASS,
                }
            ),
            'back_image': forms.FileInput(
                attrs={
                    'accept': 'image/jpeg,image/png,.jpg,.jpeg,.png',
                    'class': DOCUMENT_FILE_INPUT_CLASS,
                }
            ),
        }

    def _clean_image(self, field_name):
        image = self.cleaned_data.get(field_name)
        if not image:
            return image
        content_type = getattr(image, 'content_type', '')
        if content_type not in self.ALLOWED_IMAGE_TYPES:
            raise forms.ValidationError('Only JPG and PNG images are accepted.')
        if hasattr(image, 'size') and image.size > self.MAX_IMAGE_SIZE:
            raise forms.ValidationError('File size must be 10MB or less.')
        return image

    def clean_front_image(self):
        return self._clean_image('front_image')

    def clean_back_image(self):
        return self._clean_image('back_image')

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance

        if not cleaned_data.get('document_type'):
            self.add_error('document_type', 'Please select a document type.')

        has_front = bool(
            cleaned_data.get('front_image')
            or self.existing_files.get('front_image')
            or (instance.pk and instance.front_image)
        )
        has_back = bool(
            cleaned_data.get('back_image')
            or self.existing_files.get('back_image')
            or (instance.pk and instance.back_image)
        )

        if not has_front:
            self.add_error('front_image', 'Please upload the front of your ID.')
        if not has_back:
            self.add_error('back_image', 'Please upload the back of your ID.')

        return cleaned_data


class KYCLivenessForm(forms.ModelForm):
    def __init__(self, *args, existing_selfie=None, **kwargs):
        self.existing_selfie = existing_selfie
        super().__init__(*args, **kwargs)
        if not (self.instance and self.instance.selfie_image) and not self.existing_selfie:
            self.fields['selfie_image'].required = True

    class Meta:
        model = KYCDocument
        fields = ['selfie_image']
        widgets = {
            'selfie_image': forms.FileInput(
                attrs={
                    'accept': 'image/jpeg,image/png,.jpg,.jpeg,.png',
                    'class': DOCUMENT_FILE_INPUT_CLASS,
                }
            ),
        }

    def clean_selfie_image(self):
        image = self.cleaned_data.get('selfie_image')
        if image is None and self.existing_selfie:
            return None
        if image and hasattr(image, 'size') and image.size > KYCDocumentForm.MAX_IMAGE_SIZE:
            raise forms.ValidationError('File size must be 10MB or less.')
        return image


class KYCFinalizeForm(forms.Form):
    confirm_data = forms.BooleanField(required=True)
    agree_terms = forms.BooleanField(required=True)


class UserCreateForm(UserCreationForm):
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


class UserRoleSelectionForm(UserCreationForm):
    """Registration form: role removed, new users default to 'client' group."""
    email = forms.EmailField(required=True, help_text='A valid email address.')

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            try:
                group = Group.objects.get(name='client')
                user.groups.add(group)
            except Group.DoesNotExist:
                # If the 'client' group isn't present, just continue without failing.
                pass
        return user


class UserUpdateForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'size': 4})
    )

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'is_active', 'is_staff', 'is_superuser', 'groups')