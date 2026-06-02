from django.contrib import admin
from .models import KYCProfile, KYCDocument


admin.site.register(KYCProfile)
admin.site.register(KYCDocument)