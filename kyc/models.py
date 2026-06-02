from django.db import models
from django.contrib.auth.models import User


class KYCProfile(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Resubmission Required', 'Resubmission Required'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=30, choices=GENDER_CHOICES, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    street_address = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class KYCDocument(models.Model):
    DOCUMENT_TYPES = [
        ('National ID', 'National ID'),
        ('Driver License', 'Driver License'),
        ('Passport', 'Passport'),
        ('Student ID', 'Student ID'),
    ]

    profile = models.ForeignKey(KYCProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    id_number = models.CharField(max_length=100, blank=True)

    front_image = models.ImageField(upload_to='kyc/front_ids/', blank=True, null=True)
    back_image = models.ImageField(upload_to='kyc/back_ids/', blank=True, null=True)
    selfie_image = models.ImageField(upload_to='kyc/selfies/', blank=True, null=True)

    remarks = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.full_name} - {self.document_type}"


class KYCApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_applications')
    profile = models.OneToOneField(KYCProfile, on_delete=models.CASCADE, related_name='application')
    document = models.OneToOneField(KYCDocument, on_delete=models.CASCADE, related_name='application')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"