from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class GlobalLoginRequiredMiddleware:
    """
    Middleware that forces login for all views except:
    - The login URL itself.
    - Static files (CSS, JS, Images).
    - Admin site (optional, but we keep it protected by default).
    - Health check endpoint (for Render deployment).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URLs that do NOT require login
        whitelist = [
            reverse('login'),           # The login page
            '/static/',                 # Static files
            '/admin/',                  # Django admin (optional, can be removed)
            '/health/',                 # Render health check (we will add this later)
        ]

        # Check if the requested path is in the whitelist
        is_whitelisted = any(request.path.startswith(url) for url in whitelist)

        # If user is not authenticated and not on a whitelisted path, redirect to login
        if not request.user.is_authenticated and not is_whitelisted:
            return redirect('login')

        # Otherwise, continue processing the request
        response = self.get_response(request)
        return response