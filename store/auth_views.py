from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from firebase_admin import auth
import json


@csrf_exempt
def login_redirect(request):
    if request.method == "POST":
        data = json.loads(request.body)
        token = data.get("token")

        try:
            decoded_token = auth.verify_id_token(token)
            request.session["user"] = decoded_token
            last_page = request.session.get("last_page", "/")
            return JsonResponse({"redirect_url": last_page})
        except:
            return JsonResponse({"error": "Invalid token"}, status=401)

    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def protected_view(request):
    user = request.session.get("user", None)
    if user:
        return JsonResponse({"user": user})
    return JsonResponse({"error": "Unauthorized"}, status=401)

@csrf_exempt
def logout_view(request):
    request.session.flush()
    return JsonResponse({"message": "Logged out"})