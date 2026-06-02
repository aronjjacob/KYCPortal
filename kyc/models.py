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

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    address = models.TextField()
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

    front_image = models.ImageField(upload_to='kyc/front_ids/')
    back_image = models.ImageField(upload_to='kyc/back_ids/')
    selfie_image = models.ImageField(upload_to='kyc/selfies/')

    remarks = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.full_name} - {self.document_type}"