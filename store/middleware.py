from django.http import JsonResponse
from firebase_admin import auth
from django.utils.deprecation import MiddlewareMixin

class FirebaseAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_token = request.COOKIES.get("authToken")  # Get token from cookies

        if auth_token:
            try:
                decoded_token = auth.verify_id_token(auth_token)
                print(f"Authenticated User: {decoded_token}")  # Debugging log
                request.user = decoded_token  # Set Firebase user
            except Exception as e:
                print("Invalid Firebase token:", e)
                # Handle invalid token by denying access with a JsonResponse or similar
                return JsonResponse({'error': 'Invalid token, please login again.'}, status=401)
        else:
            # If no token is found, ensure the user is set to None
            request.user = None
