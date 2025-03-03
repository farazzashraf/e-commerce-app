from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
from firebase_admin import auth, credentials
import firebase_admin
from pymongo import MongoClient
import traceback
from django.views.decorators.csrf import csrf_exempt
import logging
from django.contrib.auth import logout
from firebase_admin import db
import re
import dns.resolver
import supabase
from django.core.files.storage import FileSystemStorage
import os
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import datetime
from django.contrib import messages
from functools import wraps
import logging
from django.urls import reverse
from .services.supabase_client import supabase
# Make sure to create a ProductForm for your form handling
from .services.supabase_client import create_user, upload_image, add_product as supabase_add_product, fetch_all_products, delete_product
from .services.supabase_client import fetch_product_details, update_product, fetch_user_by_uid, get_promo_code_details
from django.http import HttpResponse
import uuid
from supabase import create_client
from .services.supabase_client import CartService


# Load environment variables from .env file
# load_dotenv()
logger = logging.getLogger(__name__)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load .env
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path)


# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


ADMIN_EMAIL = os.getenv("ADMIN_MAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_UID = os.getenv("ADMIN_UID")


def has_valid_mx_record(email):
    """ Check if the domain of the email has a valid MX record """
    try:
        domain = email.split("@")[-1]
        records = dns.resolver.resolve(domain, 'MX')
        return bool(records)  # Returns True if MX records exist
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        return False


def is_valid_email(email):
    """ Validate email format using regex """
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email) is not None


# Set up logging

# Ensure Firebase is initialized only once
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("firebase/firebase-admin-sdk.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.error(f"Firebase initialization error: {e}")
        raise


# Function to check if email already exists


def is_email_registered(email):
    try:
        # Try to get the user by email
        user = auth.get_user_by_email(email)
        return True  # Email is registered
    except auth.UserNotFoundError:
        return False  # Email is not registered


def check_email(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")

            # Validate email format
            if not is_valid_email(email):
                return JsonResponse({"success": False, "error": "Invalid email format."}, status=400)

            # Check if the domain has a valid mail server
            if not has_valid_mx_record(email):
                return JsonResponse({"success": False, "error": "Email domain does not exist."}, status=400)

            if email and is_email_registered(email):
                return JsonResponse({"success": False, "error": "Email is already registered."}, status=400)
            else:
                return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)

@csrf_exempt
def firebase_auth(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        id_token = data.get("token")
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]

        # Merge anonymous cart with Supabase cart
        session_cart = request.session.get('cart', {})
        if session_cart:
            # Get existing user cart
            supabase_cart = supabase.table('carts').select(
                '*').eq('user_id', uid).execute().data
            supabase_cart = {item['product_id']
                : item for item in supabase_cart}

            # Merge carts
            for product_id, item in session_cart.items():
                if product_id in supabase_cart:
                    new_quantity = supabase_cart[product_id]['quantity'] + \
                        item['quantity']
                    supabase.table('carts').update({'quantity': new_quantity}).eq(
                        'user_id', uid).eq('product_id', product_id).execute()
                else:
                    supabase.table('carts').insert({
                        'user_id': uid,
                        'product_id': product_id,
                        'name': item['name'],
                        'price': item['price'],
                        'image_url': item['image_url'],
                        'quantity': item['quantity']
                    }).execute()

            # Clear session cart
            del request.session['cart']

        # Set up session
        request.session.flush()
        request.session["uid"] = uid
        request.session.modified = True

        return JsonResponse({"success": True, "uid": uid})

    except Exception as e:
        logger.error(f"Error in firebase_auth: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

def home(request):
    """Home Page - Redirects unauthenticated users to login"""
    uid = request.session.get("uid")
    logger.info(f"User ID: {uid}")

    if not uid:
        return redirect("/login/")  # Redirect unauthenticated users
    
    user_name = fetch_user_by_uid(uid)
    print(f"🔍 User name in view: {user_name}")

    # Fetch products from Supabase
    products = fetch_all_products()

    return render(request, "store/home.html", {"products": products, "user_name": user_name})


def login_required(view_func):
    """ Middleware to restrict access to authenticated users only """
    def wrapper(request, *args, **kwargs):
        if not request.session.get("uid"):  # ✅ Safe session check
            return redirect("/login/")
        return view_func(request, *args, **kwargs)
    return wrapper

def signup_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # 🛠 Debugging
            print("Received raw data:", request.body.decode(
                "utf-8"))  # Log raw JSON
            print("Parsed data:", data)  # Log parsed JSON

            uid = data.get("uid")  # 🔹 Firebase UID
            name = data.get("name")
            phone = data.get("phone")
            email = data.get("email")

            if not all([uid, name, phone, email]):
                print(
                    f"Missing field detected: UID={uid}, Name={name}, Phone={phone}, Email={email}")
                return JsonResponse({"success": False, "error": "All fields are required."}, status=400)

            print(
                f"Received signup data: UID={uid}, Name={name}, Phone={phone}, Email={email}")

            # 🔹 Insert into Supabase
            supabase_response = create_user(uid, name, phone, email)
            if not supabase_response:
                print("Supabase insert failed.")
                return JsonResponse({"success": False, "error": "Error storing user data in Supabase."}, status=500)

            print("User successfully inserted into Supabase!")
            return JsonResponse({"success": True, "message": "Account created successfully!"})

        except json.JSONDecodeError:
            print("Error: Invalid JSON format received")
            return JsonResponse({"success": False, "error": "Invalid JSON format."}, status=400)

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({"success": False, "error": "Failed to create an account. Please try again."}, status=500)

    return render(request, "store/signup.html")

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            # Firebase Authentication using email and password
            user = auth.get_user_by_email(email)

            if user:
                # Clear any existing session data from previous user
                request.session.flush()  # This clears the entire session

                # Set session data for the new user
                request.session["uid"] = user.uid
                request.session.modified = True  # Ensure session is saved
                request.session.set_expiry(0)  # Optional: set session expiry

                # Initialize an empty cart for the new user, tied to their unique UID
                request.session[f'cart_{user.uid}'] = {}

                # Redirect to home page after login
                return redirect("home")

        except auth.UserNotFoundError:
            return render(request, "store/login.html", {"error_message": "Invalid email or password"})
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return render(request, "store/login.html", {"error_message": "Something went wrong. Please try again."})

    return render(request, "store/login.html")

def logout_view(request):
    # Preserve anonymous cart if exists
    anonymous_cart = request.session.get('cart', {})

    # Clear session
    request.session.flush()

    # Restore anonymous cart if user wasn't logged in
    if anonymous_cart and not request.session.get("uid"):
        request.session['cart'] = anonymous_cart

    return redirect('home')


def save_last_page(request):
    """ Save the last visited page in session """
    request.session["last_page"] = request.path


def add_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = str(data.get('product_id'))
            uid = request.session.get("uid")

            # Extract only the image path before storing
            image_path = data.get("image_url", "")

            # Session cart handling for anonymous users
            if not uid:
                cart = request.session.get('cart', {})
                cart_item = cart.get(product_id, {
                    'name': data.get('name'),
                    'category': data.get('category'),
                    'price': float(data.get('price')),
                    'image_url': image_path,
                    'quantity': 0
                })
                cart_item['quantity'] += int(data.get('quantity', 1))
                cart[product_id] = cart_item
                request.session['cart'] = cart
                request.session.modified = True
                return JsonResponse({'success': True})

            # Authenticated users
            CartService.add_to_cart(
                uid,
                product_id,
                {
                    'name': data.get('name'),
                    'price': float(data.get('price')),
                    'category': data.get('category'),
                    # 'image_url': data.get('image_url'),
                    'image_url': image_path,
                    'quantity': int(data.get('quantity', 1))
                }
            )
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def remove_from_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = str(data.get('product_id'))
            uid = request.session.get("uid")

            if uid:
                CartService.remove_from_cart(uid, product_id)
            else:
                cart = request.session.get('cart', {})
                if product_id in cart:
                    del cart[product_id]
                    request.session['cart'] = cart
                    request.session.modified = True

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def update_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = str(data.get('product_id'))
            action = data.get('action')
            uid = request.session.get("uid")

            if uid:
                # Get current quantity from Supabase
                items = CartService.get_cart_items(uid)
                current = next(
                    (item for item in items if item['product_id'] == product_id), None)
                if not current:
                    return JsonResponse({'success': False, 'error': 'Item not found'})

                new_quantity = current['quantity'] + \
                    (1 if action == 'increase' else -1)
                if new_quantity <= 0:
                    CartService.remove_from_cart(uid, product_id)
                else:
                    CartService.update_cart_quantity(
                        uid, product_id, new_quantity)
            else:
                # Session handling
                cart = request.session.get('cart', {})
                if product_id in cart:
                    if action == 'increase':
                        cart[product_id]['quantity'] += 1
                    elif action == 'decrease':
                        cart[product_id]['quantity'] -= 1
                        if cart[product_id]['quantity'] <= 0:
                            del cart[product_id]
                    request.session['cart'] = cart
                    request.session.modified = True

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def cart_view(request):
    uid = request.session.get("uid")
    try:
        if uid:
            # Get cart items and convert to {product_id: item} format
            items = CartService.get_cart_items(uid)
            cart_data = {item['product_id']: item for item in items}
        else:
            cart_data = request.session.get('cart', {})

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'cart': cart_data}, safe=False)
        return render(request, "store/cart.html", {"cart": cart_data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def cart_count(request):
    try:
        uid = request.session.get("uid")
        count = CartService.get_cart_count(uid) if uid else sum(
            item['quantity'] for item in request.session.get('cart', {}).values())
        return JsonResponse({'cart_count': count})
    except Exception as e:
        return JsonResponse({'cart_count': 0})


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_authenticated'):
            return redirect(reverse('admin_login'))
        return view_func(request, *args, **kwargs)
    return wrapper


@csrf_exempt
def admin_login(request):
    if request.method == "GET":
        return render(request, "store/admin_login.html")

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        id_token = data.get("token")

        if not id_token:
            logger.warning("❌ No token provided in request")
            return JsonResponse({"error": "No token provided"}, status=400)

        # Log the token for debugging (remove in production!)
        # Log only first 50 chars
        logger.info(f"🔑 Received Firebase ID Token: {id_token[:50]}...")

        # Verify Firebase ID token
        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")

            logger.info(
                f"✅ Firebase authentication successful: {email} ({uid})")
        except auth.InvalidIdTokenError:
            logger.error("❌ Invalid Firebase ID token")
            return JsonResponse({"error": "Invalid token"}, status=401)
        except auth.ExpiredIdTokenError:
            logger.error("❌ Expired Firebase ID token")
            return JsonResponse({"error": "Expired token"}, status=401)
        except firebase_admin.exceptions.FirebaseError as e:
            logger.error(f"❌ Firebase Auth error: {str(e)}")
            return JsonResponse({"error": "Authentication failed"}, status=401)

        # Ensure the authenticated user is the admin
        if uid == ADMIN_UID:
            request.session["admin_authenticated"] = True
            request.session["admin_uid"] = uid
            return JsonResponse({"success": True, "redirect": "/store-admin/dashboard/"})
        else:
            logger.warning(f"❌ Unauthorized login attempt by {email} ({uid})")
            return JsonResponse({"error": "Unauthorized access"}, status=403)

    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON format in request body")
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        logger.error(f"❌ Unexpected error in admin_login: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')


@admin_required
@csrf_exempt
def add_product_view(request):
    if request.method == 'GET':
        # Render the template for GET requests
        return render(request, 'store/add_product.html')

    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get("category")
        price = float(request.POST.get('price'))  # ✅ Convert string to float
        description = request.POST.get('description')
        image = request.FILES.get('image')

        admin_id = request.session.get('admin_uid')
        print(f"🔹 Admin ID from session: {admin_id}")  # Debugging

        if not admin_id:
            return JsonResponse({"error": "Admin ID is missing."}, status=400)

        try:
            image_url = upload_image(image)

            product = supabase_add_product(
                name, category, price, description, image_url, admin_id)
            print(f"🔹 Supabase Insert Response: {product}")  # Debugging
            if product:
                # Success message
                messages.success(request, "Product added successfully!")
                return JsonResponse({"success": True}, status=200)
            else:
                return JsonResponse({"error": "Failed to add product."}, status=500)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def update_product_view(request, product_id):
    """Render update product form with existing product details and handle form submission."""

    product = fetch_product_details(product_id)

    if "error" in product:
        messages.error(request, "Failed to fetch product details.")
        return JsonResponse({"error": "Failed to fetch product details."}, status=400)

    if request.method == "POST":
        name = request.POST.get("name")
        category = request.POST.get("category")
        price = request.POST.get("price")
        description = request.POST.get("description")
        image_file = request.FILES.get("image")

        # Log form data for debugging
        print("Form data:", name, category, price, description, image_file)

        update_response = update_product(
            product_id, name=name, category=category, price=price,
            description=description, image_file=image_file
        )

        # Log the update response for debugging
        print("Update Response:", update_response)

        if "error" in update_response:
            messages.error(request, update_response["error"])
            return JsonResponse({"error": update_response["error"]}, status=400)
        else:
            messages.success(request, "Product updated successfully!")
            return JsonResponse({"success": "Product updated successfully!"}, status=200)

    return render(request, "store/admin_update_product.html", {"product": product})

@admin_required
def admin_dashboard(request):
    """Fetch products from Supabase and render admin dashboard."""
    try:
        products_list = fetch_all_products()
        return render(request, 'store/admin_dashboard.html', {'products': products_list})
    except Exception as e:
        messages.error(request, f'Error fetching products: {str(e)}')
        return render(request, 'store/admin_dashboard.html', {'products': []})


def delete_product_view(request, product_id):
    """View function to delete a product and redirect to the dashboard."""
    return delete_product(request, product_id)  # Call the helper function