from django.shortcuts import redirect
from django.urls import reverse


class RoleBasedRedirectMiddleware:
    """Redirect users trying to access wrong dashboard to their role-appropriate one."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Paths that require specific roles
        self.role_paths = {
            'client': ['/kyc/client/', '/kyc/upload/', '/kyc/documents/', '/kyc/liveness/', '/kyc/finalize/', '/kyc/status/'],
            'verifier': ['/kyc/verifier/', '/kyc/review-queue/', '/kyc/document-review/', '/kyc/verification-history/'],
            'admin': ['/kyc/admin/', '/kyc/admin-dashboard/', '/kyc/user-management/', '/kyc/document-review-admin/', '/kyc/bulk-update/'],
        }

    def __call__(self, request):
        if request.user.is_authenticated:
            current_path = request.path
            user_has_admin = request.user.is_staff or request.user.is_superuser
            user_is_verifier = request.user.groups.filter(name='verifier').exists()
            user_is_client = request.user.groups.filter(name='client').exists()

            # Check if user is trying to access restricted paths
            for role, paths in self.role_paths.items():
                for path in paths:
                    if current_path.startswith(path):
                        if role == 'admin' and not user_has_admin:
                            return redirect('client_dashboard' if user_is_client else 'verifier_dashboard')
                        elif role == 'verifier' and not user_is_verifier and not user_has_admin:
                            return redirect('client_dashboard' if user_is_client else 'login')
                        elif role == 'client' and not user_is_client and not user_has_admin:
                            return redirect('verifier_dashboard' if user_is_verifier else 'login')

        response = self.get_response(request)
        return response
