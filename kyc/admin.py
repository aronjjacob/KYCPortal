from django.contrib import admin
from .models import KYCProfile, KYCDocument, AdminDashboardFeature


class AdminDashboardFeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description', 'url_name')
    ordering = ('order', 'created_at')
    fieldsets = (
        ('Feature Details', {
            'fields': ('title', 'description', 'url_name', 'icon')
        }),
        ('Status', {
            'fields': ('is_active', 'order')
        }),
    )


admin.site.register(KYCProfile)
admin.site.register(KYCDocument)
admin.site.register(AdminDashboardFeature, AdminDashboardFeatureAdmin)