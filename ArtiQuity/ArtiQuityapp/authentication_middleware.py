from django.shortcuts import redirect
from .models import User

class CustomAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.session.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                user.is_authenticated = True
                request.user = user
            except User.DoesNotExist:
                request.user = None
        else:
            request.user = None

        response = self.get_response(request)
        return response
