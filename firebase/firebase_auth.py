from firebase_admin import auth

def verify_firebase_token(token):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token  # This contains user info
    except Exception:
        return None
