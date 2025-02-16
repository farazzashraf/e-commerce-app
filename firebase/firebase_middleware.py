from django.http import JsonResponse
from firebase.firebase_auth import verify_firebase_token


class FirebaseAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.headers.get("Authorization")

        if token:
            user_data = verify_firebase_token(token)
            if user_data:
                request.user = user_data  # Attach Firebase user data
            else:
                return JsonResponse({"error": "Invalid token"}, status=401)

        return self.get_response(request)
