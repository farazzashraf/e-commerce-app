from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from firebase_admin import auth, credentials
import firebase_admin
from pymongo import MongoClient
from django.views.decorators.csrf import csrf_exempt
import logging
from django.contrib.auth import logout
import re
import dns.resolver
import supabase
import os
from dotenv import load_dotenv
from decimal import Decimal
import datetime
from django.utils import timezone
from django.contrib import messages
from functools import wraps
import logging
from django.urls import reverse
from .services.supabase_client import supabase
from django.http import HttpResponseRedirect
from django.utils.http import urlsafe_base64_encode
from supabase import create_client
from django.core.mail import send_mail
from django.conf import settings
from .services.orm_queries import CartService
import difflib
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from django.conf.urls.static import static
from django.db.models import Sum, Count, Avg


import traceback
# Ensure your Order model is correctly imported
from store.models import Order, Product, User, Cart, OrderItem, AdminStore, Category, Subcategory
from store.services.orm_queries import (create_user, get_user_by_uid, get_all_products, orm_add_product, fetch_all_products,
                                        delete_product, orm_update_product, fetch_product_details_orm, get_promo_code_details,
                                        get_products_by_ids, create_order, create_order_items,
                                        delete_purchased_products, delete_order, get_user_email, get_order_by_id,
                                        update_order_status, get_order_items, get_all_orders, get_order_items_with_details, extract_customer_name,
                                        get_all_orders_for_admin, get_user_orders, create_admin_store_record, get_public_logo_url)
from django.db.models import Q
from django.template.loader import render_to_string
from django.contrib.auth import authenticate
from django.contrib.auth import authenticate, login
from django.core.cache import cache

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


ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_UID = os.getenv("ADMIN_UID")


def clear_products_cache():
    cache.delete("all_products_with_variants")


def seller_approved_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            # Look up the seller record based on the logged-in user's email.
            seller = AdminStore.objects.get(email=request.user.email)
            if not seller.is_approved:
                # Render a page that informs the seller their account is pending approval.
                return render(request, "store/admin/pending_approval.html", {
                    "message": "Your seller account is pending approval. Please wait for an admin to approve your account."
                })
        except AdminStore.DoesNotExist:
            messages.error(
                request, "Seller account not found. Please sign up as a seller.")
            return redirect("seller_signup")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def check_login_status(request):
    is_logged_in = request.session.get("uid") is not None
    return JsonResponse({"is_logged_in": is_logged_in})


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
                return JsonResponse({"success": True, 'message': 'Email checked'})

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

        # --- MERGE CART LOGIC ---
        session_cart = request.session.get('cart', {})
        if session_cart:
            # Fetch the User instance using the uid
            # Ensure we have a valid User instance
            user = get_object_or_404(User, id=uid)

            # Fetch existing cart items for the user
            supabase_cart = Cart.objects.filter(user_id=user)
            # Use product_id.id to compare properly
            supabase_cart_dict = {
                item.product_id.id: item for item in supabase_cart}

            for product_id, item in session_cart.items():
                product = get_object_or_404(
                    Product, id=product_id)  # Ensure product exists

                if product.id in supabase_cart_dict:
                    # Update quantity if product already exists in the cart
                    cart_item = supabase_cart_dict[product.id]
                    cart_item.quantity += item['quantity']
                    cart_item.save()
                else:
                    # Create a new cart entry if product is not in the cart
                    Cart.objects.create(
                        user_id=user,  # Pass the User instance
                        product_id=product,  # Pass the Product instance
                        name=item['name'],
                        price=item['price'],
                        image_url=item['image_url'],
                        quantity=item['quantity']
                    )

            # Clear session cart after merging
            del request.session['cart']
        # --- END MERGE CART LOGIC ---

        # Set up session
        request.session.flush()
        request.session["uid"] = uid
        request.session.modified = True

        # Admin check: If the UID matches the admin UID, set additional admin session data
        if uid == ADMIN_UID:
            request.session["admin_authenticated"] = True
            request.session["admin_uid"] = uid
            # Return a JSON response that instructs the frontend to redirect to the admin dashboard.
            return JsonResponse({"success": True, "redirect": "/store-admin/dashboard/", "uid": uid})

        # For normal users, return success without a redirect field
        return JsonResponse({"success": True, "uid": uid})

    except Exception as e:
        logger.error(f"Error in firebase_auth: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def fuzzy_search(query, text, threshold=0.5):
    """
    Returns True if the query approximately matches any word in text.
    First, it checks for an exact substring match. Otherwise, it splits the text
    into words and returns True if any word has a similarity ratio above the threshold.
    """
    if query in text:
        return True
    for word in text.split():
        if difflib.SequenceMatcher(None, query, word).ratio() >= threshold:
            return True
    return False


def home(request):
    """Home Page - Allow all users to browse, require login only on interaction"""
    uid = request.session.get("uid")
    logger.info(f"User ID: {uid}")

    # Fetch user details
    user = get_user_by_uid(uid) if uid else None
    user_name = user.name if user else None
    user_email = user.email if user else None

    # Fetch all products (assumed to include keys like category__slug, etc.)
    products = get_all_products()

    # Get selected filters from query parameters (using slugs)
    selected_category = request.GET.get('category')
    selected_subcategory = request.GET.get('subcategory')

    # Fetch active categories with their subcategories
    categories = Category.objects.filter(is_active=True).prefetch_related(
        Prefetch('subcategories',
                 queryset=Subcategory.objects.filter(is_active=True))
    )

    if selected_category:
        products = [
            p for p in products
            if p.get("category__slug", "").lower() == selected_category.lower()
        ]

    if selected_subcategory:
        products = [
            p for p in products
            if p.get("subcategory__slug", "").lower() == selected_subcategory.lower()
        ]

    # Search query across relevant fields (adjust field names if needed)
    query = request.GET.get("q", "").strip()
    if query:
        query = query.lower()
        products = [
            p for p in products if any(
                fuzzy_search(query, str(p[field]).lower())
                for field in [
                    "name", "category__name", "description", "price",
                    "original_price", "created_at", "image_url",
                    "image_url2", "image_url3", "image_url4"
                ] if p.get(field)
            )
        ]

    # Retrieve and apply sort option
    sort_option = request.GET.get("sort", "featured")
    if sort_option == "price-low":
        products.sort(key=lambda p: p.get("price", 0))
    elif sort_option == "price-high":
        products.sort(key=lambda p: p.get("price", 0), reverse=True)
    elif sort_option == "newest":
        products.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    # For 'featured' or any other sort, you can add additional sorting logic here

    # --- Fetch all approved sellers (stores) ---
    sellers = AdminStore.objects.filter(
        is_approved=True).order_by('company_name')
    logger.debug(f"Sellers count: {sellers.count()}")

    context = {
        "products": products,
        "user_name": user_name,
        "user_email": user_email,
        "query": query,
        "sort_option": sort_option,
        "categories": categories,
        "selected_category": selected_category,
        "selected_subcategory": selected_subcategory,
        "sellers": sellers,  # Pass the sellers queryset here.
    }

    return render(
        request,
        "store/home.html",
        context
    )


def api_products(request):
    products = fetch_all_products()

    return JsonResponse(products, safe=False)


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

            # 🔹 Verify Firebase UID before inserting into the database
            try:
                user_record = auth.get_user(uid)
                is_verified = user_record.email_verified  # ✅ Get verification status
            except firebase_admin.auth.AuthError:
                return JsonResponse({"success": False, "error": "Invalid Firebase user."}, status=400)

            # 🔹 Store user in Django ORM (which will save to Supabase via PostgreSQL)
            user = create_user(uid, name, phone, email, is_verified)

            if user is None:
                return JsonResponse({"success": False, "error": "User already exists."}, status=400)

            print("User successfully inserted into the database!")
            return JsonResponse({"success": True, "message": "Account created successfully!"})

        except json.JSONDecodeError:
            print("Error: Invalid JSON format received")
            return JsonResponse({"success": False, "error": "Invalid JSON format."}, status=400)

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({"success": False, "error": "Failed to create an account. Please try again."}, status=500)

    return render(request, "store/signup.html")


def update_verification(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            uid = data.get("uid")
            is_verified = data.get("is_verified")

            if not uid:
                return JsonResponse({"success": False, "error": "UID is required."}, status=400)

            # 🔹 Update Supabase
            response = supabase.table("users").update(
                {"is_verified": is_verified}).eq("id", uid).execute()
            print("🔄 Supabase Update Response:", response)

            return JsonResponse({"success": True, "message": "User verification status updated."})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            # Retrieve the user using Firebase
            user = auth.get_user_by_email(email)  # Get user details

            logger.info(f"🔍 Login attempt: {email} (UID: {user.uid})")

            # Debug: Print the expected admin UID
            logger.info(f"🔍 Expected ADMIN_UID: {ADMIN_UID}")

            # Check if the user is an admin
            if user.uid == ADMIN_UID:
                logger.info("✅ Admin login detected!")
                request.session.flush()
                request.session["admin_authenticated"] = True
                request.session["admin_uid"] = user.uid
                request.session.modified = True
                # Redirect admin to dashboard
                return redirect("/store-admin/dashboard/")

            # Normal user authentication
            request.session.flush()
            request.session["uid"] = user.uid
            request.session.modified = True
            request.session.set_expiry(0)

            # Initialize an empty cart for the user
            request.session[f'cart_{user.uid}'] = {}

            logger.info("✅ Normal user login successful!")
            return redirect("/")  # Redirect normal users to home

        except auth.UserNotFoundError:
            logger.error("❌ Invalid email or password")
            return render(request, "store/login.html", {"error_message": "Invalid email or password"})
        except Exception as e:
            logger.error(f"❌ Error during login: {str(e)}")
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

    return redirect('login')


def save_last_page(request):
    """ Save the last visited page in session """
    request.session["last_page"] = request.path


def add_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = int(data.get('product_id'))  # Convert to integer
            uid = request.session.get("uid")
            image_path = data.get("image_url", "")

            if not uid:
                # Convert product_id to string for session consistency
                str_pid = str(product_id)
                cart = request.session.get('cart', {})
                cart_item = cart.get(str_pid, {
                    'name': data.get('name'),
                    'category': data.get('category'),
                    'price': float(data.get('price')),
                    'image_url': image_path,
                    'quantity': 0
                })
                cart_item['quantity'] += int(data.get('quantity', 1))
                cart[str_pid] = cart_item
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
                    'image_url': image_path,
                    'quantity': int(data.get('quantity', 1))
                }
            )
            return JsonResponse({'success': True})

        except ValueError as ve:
            # Handle stock errors without "Invalid ID" prefix
            error_msg = str(ve)
            if "available" in error_msg or "add" in error_msg:
                return JsonResponse({'success': False, 'error': error_msg})
            return JsonResponse({'success': False, 'error': f"Invalid ID: {error_msg}"})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def cart_view(request):
    uid = request.session.get("uid")

    try:
        if uid:
            items = CartService.get_cart_items(uid)
            # Convert to same format as session cart
            cart_data = {
                str(item['product_id__id']): {  # Convert to string
                    'name': item['name'],
                    'category': item['category'],
                    'price': float(item['price']),
                    'image_url': item['image_url'],
                    'quantity': item['quantity'],
                    'seller_name': item.get('product_id__admin_id__company_name', 'Unknown Seller')
                }
                for item in items
            }
        else:
            cart_data = request.session.get('cart', {})

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'cart': cart_data}, safe=False)
        return render(request, "store/cart.html", {"cart": cart_data})

    except Exception as e:
        print(f"Cart view error: {str(e)}")  # Add logging
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def remove_from_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = int(data.get('product_id'))  # Convert to integer
            uid = request.session.get("uid")

            if uid:
                user = User.objects.get(id=uid)
                product = Product.objects.get(id=product_id)
                Cart.objects.filter(user_id=user, product_id=product).delete()
            else:
                str_pid = str(product_id)
                cart = request.session.get('cart', {})
                if str_pid in cart:
                    del cart[str_pid]
                    request.session['cart'] = cart
                    request.session.modified = True

            return JsonResponse({'success': True})

        except (User.DoesNotExist, Product.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Invalid ID'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def update_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = int(data.get('product_id'))  # Convert to integer
            action = data.get('action')
            uid = request.session.get("uid")

            if uid:
                items = CartService.get_cart_items(uid)
                # Use product_id__id from the ORM response
                current = next(
                    (item for item in items if item['product_id__id'] == product_id), None)
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
                # Convert to string for session consistency
                str_pid = str(product_id)
                cart = request.session.get('cart', {})
                if str_pid in cart:
                    if action == 'increase':
                        cart[str_pid]['quantity'] += 1
                    elif action == 'decrease':
                        cart[str_pid]['quantity'] -= 1
                        if cart[str_pid]['quantity'] <= 0:
                            del cart[str_pid]
                    request.session['cart'] = cart
                    request.session.modified = True

            return JsonResponse({'success': True})

        except ValueError as ve:
            return JsonResponse({'success': False, 'error': f'Invalid product ID: {str(ve)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def cart_count(request):
    try:
        uid = request.session.get("uid")
        if uid:
            count = CartService.get_cart_count(uid) or 0
        else:
            count = sum(item['quantity']
                        for item in request.session.get('cart', {}).values())
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
        return render(request, "store/admin/admin_login.html")

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        id_token = data.get("token")

        if not id_token:
            logger.warning("❌ No token provided in request")
            return JsonResponse({"error": "No token provided"}, status=400)

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

        # Look up the admin user by email from your AdminStore model
        try:
            admin_user = AdminStore.objects.get(email=email)
        except AdminStore.DoesNotExist:
            logger.warning(f"❌ No admin account found for {email}")
            return JsonResponse({"error": "Unauthorized access"}, status=403)

        # # Check if the seller's account is approved
        # if not admin_user.is_approved:
        #     logger.warning(f"❌ Admin account for {email} is pending approval")
        #     return JsonResponse({"error": "Your account is pending approval. Please wait for an admin to approve your account."}, status=403)

        # If approved, set the session and allow access
        request.session["admin_authenticated"] = True
        request.session["admin_uid"] = uid
        request.session["admin_email"] = email
        return JsonResponse({"success": True, "redirect": "/store-admin/dashboard/"})

    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON format in request body")
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        logger.error(f"❌ Unexpected error in admin_login: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

# API endpoint to get all active categories


@require_http_methods(["GET"])
def get_categories(request):
    categories = Category.objects.filter(is_active=True).values('id', 'name')
    return JsonResponse(list(categories), safe=False)

# API endpoint to get subcategories for a specific category


@require_http_methods(["GET"])
def get_subcategories(request, category_id):
    subcategories = Subcategory.objects.filter(
        category_id=category_id,
        is_active=True
    ).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)


@admin_required
@csrf_exempt
def add_product_view(request):
    if request.method == 'GET':
        return render(request, 'store/admin/add_product.html')

    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        price = float(request.POST.get('price'))
        original_price = float(request.POST.get('originalprice'))
        description = request.POST.get('description')
        sizes = request.POST.get('sizes', '')
        fit = request.POST.get('fit', '')
        stock = request.POST.get('stock')

        # Get the main image and additional images (as a list)
        image = request.FILES.get('image')
        additional_images = request.FILES.getlist('additional_images')

        # Validate required fields
        if not all([name, category_id, subcategory_id, price, original_price, description]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # # Check if category and subcategory exist and are related
        # category = get_object_or_404(Category, id=category_id)
        # subcategory = get_object_or_404(Subcategory, id=subcategory_id, category=category)

        firebase_uid = request.session.get(
            'admin_uid')  # This is the Firebase UID
        print(f"🔹 Firebase UID from session: {firebase_uid}")

        if not firebase_uid:
            return JsonResponse({"error": "Admin is not authenticated."}, status=400)

        try:
            # Fetch the AdminStore record using Firebase UID
            admin_store = AdminStore.objects.get(firebase_uid=firebase_uid)
            admin_store_id = str(admin_store.id)  # Convert UUID to string
            print(f"🔹 Resolved AdminStore ID: {admin_store_id}")

            # Correctly ordered parameters when calling orm_add_product:
            product = orm_add_product(
                name,
                category_id,
                subcategory_id,
                price,
                original_price,
                description,
                sizes,  # This maps to the `size` field in your function
                fit,
                image,
                additional_images,
                admin_store_id,
                stock,
                request
            )

            if isinstance(product, dict) and not product.get("success"):
                # Return the error message properly
                return JsonResponse(product, status=400)
            if product:
                # Invalidate the cache after a successful product addition.
                clear_products_cache()

                messages.success(request, "Product added successfully!")
                return JsonResponse({"success": True}, status=200)
            else:
                return JsonResponse({"error": "Failed to add product."}, status=500)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def update_product_view(request, product_id):
    # Retrieve product details using the ORM-based helper function
    product_details = fetch_product_details_orm(product_id)
    if "error" in product_details:
        messages.error(request, product_details["error"])
        return JsonResponse({"error": product_details["error"]}, status=404)

    if request.method == "POST":
        # ... handle the update logic as before ...
        name = request.POST.get("name")
        category = request.POST.get("category")
        subcategory = request.POST.get("subcategory")
        price = request.POST.get("price")
        originalPrice = request.POST.get("originalprice")
        description = request.POST.get("description")
        sizes = request.POST.get("sizes")
        fit = request.POST.get("fit")
        stock = request.POST.get("stock")
        image_file = request.FILES.get("image")

        # Safer approach to handle additional image files
        additional_images_files = []
        for key, file in request.FILES.items():
            if key.startswith("additional_image_"):
                # Try to extract a numeric index for sorting, if possible
                try:
                    index_part = key.split('_')[-1]
                    # Only add the file if the index is numeric (otherwise ignore it)
                    if index_part.isdigit():
                        additional_images_files.append((int(index_part), file))
                except (ValueError, IndexError):
                    # If there's an error parsing the index, just ignore this file
                    continue

        # Sort the files by their numeric index and extract just the file objects
        additional_images_files = [file for _,
                                   file in sorted(additional_images_files)]

        update_response = orm_update_product(
            product_id,
            name=name,
            category=category,
            subcategory=subcategory,
            price=price,
            original_price=originalPrice,
            description=description,
            sizes=sizes,
            fit=fit,
            stock=stock,
            image_file=image_file,
            additional_images=additional_images_files
        )

        if "error" in update_response:
            messages.error(request, update_response["error"])
            return JsonResponse({"error": update_response["error"]}, status=400)
        else:
            # Invalidate the cache after updating
            clear_products_cache()

            messages.success(request, "Product updated successfully!")
            return JsonResponse({"success": "Product updated successfully!"}, status=200)

    return render(request, "store/admin/admin_update_product.html", {"product": product_details})


# @admin_required
# def admin_dashboard(request):
#     email = request.session.get("admin_email")
#     if not email:
#         messages.error(request, "No email found for your account. Please sign up as a seller.")
#         return redirect("admin_signup")

#     try:
#         seller = AdminStore.objects.get(email=email)
#         print("Seller approval status:", seller.is_approved)
#     except AdminStore.DoesNotExist:
#         messages.error(request, "Seller account not found. Please sign up as a seller.")
#         return redirect("admin_signup")

#     # Build a basic context that always includes the seller.
#     context = {'seller': seller}

#     if not seller.is_approved:
#         context = {"message": "Your account is pending approval. Please wait for an admin to approve your account."}
#         return render(request, "store/admin/admin_dashboard.html", context)

#     # If seller is approved, check for an approval message in the session.
#     approval_message = request.session.get("approval_message")
#     if approval_message:
#         context["approval_message"] = approval_message
#         # Remove the message so it only shows once.
#         del request.session["approval_message"]

#     try:
#         query = request.GET.get('q', '').strip()
#         category = request.GET.get('category', '')
#         min_price = request.GET.get('min_price', '')
#         max_price = request.GET.get('max_price', '')
#         status = request.GET.get('status', '')
#         stock_status = request.GET.get('stock_status', '')

#         # products = fetch_all_products()  # Fetch all products from Supabase

#         cache_key = "all_products_with_variants"
#         products = cache.get(cache_key)

#         if products is None:
#             print("Cache miss. Fetching from Supabase...")
#             products = fetch_all_products()  # Fetch from Supabase
#             cache.set(cache_key, products, timeout=60 * 15)  # Cache for 15 mins
#             print("Cache set successfully:", cache.get(cache_key))  # Debugging
#         else:
#             print("Cache hit. Using cached products.")

#         if query:
#             query = query.lower()
#             products = [
#                 p for p in products if any(
#                     fuzzy_search(query, str(p[field]).lower())
#                     for field in ["id", "name", "category", "description"] if p.get(field)
#                 )
#             ]

#         # Filter by category
#         if category:
#             products = [p for p in products if p.get('category') == category]

#         # Filter by price range
#         if min_price and min_price.isdigit():
#             products = [p for p in products if float(p.get('price', 0)) >= float(min_price)]

#         if max_price and max_price.isdigit():
#             products = [p for p in products if float(p.get('price', 0)) <= float(max_price)]

#         # Filter by availability status
#         if status:
#             if status == 'available':
#                 products = [p for p in products if p.get('is_active', False)]
#             elif status == 'sold':
#                 products = [p for p in products if not p.get('is_active', True)]

#         # Filter by stock level
#         if stock_status:
#             if stock_status == 'low':
#                 products = [p for p in products if int(p.get('stock', 0)) <= 10]
#             elif stock_status == 'out':
#                 products = [p for p in products if int(p.get('stock', 0)) == 0]
#             elif stock_status == 'in':
#                 products = [p for p in products if int(p.get('stock', 0)) > 10]

#         # Get unique categories for filter dropdown
#         all_categories = sorted(set(p.get('category') for p in fetch_all_products() if p.get('category')))

#         # Existing filter code...
#         sort_by = request.GET.get('sort_by', 'id_asc')

#         # Apply sorting after all filters
#         if sort_by:
#             if sort_by == 'id_asc':
#                 products = sorted(products, key=lambda p: int(p.get('id', 0)))
#             elif sort_by == 'id_desc':
#                 products = sorted(products, key=lambda p: int(p.get('id', 0)), reverse=True)
#             elif sort_by == 'price_asc':
#                 products = sorted(products, key=lambda p: float(p.get('price', 0)))
#             elif sort_by == 'price_desc':
#                 products = sorted(products, key=lambda p: float(p.get('price', 0)), reverse=True)
#             elif sort_by == 'stock_asc':
#                 products = sorted(products, key=lambda p: int(p.get('stock', 0)))
#             elif sort_by == 'stock_desc':
#                 products = sorted(products, key=lambda p: int(p.get('stock', 0)), reverse=True)

#         # ✅ If AJAX request, return both `#productListDesktop` and `#productListMobile` content
#         if request.headers.get("X-Requested-With") == "XMLHttpRequest":
#             html_desktop = render_to_string("store/admin_partials/admin_product_list_desktop.html", {"products": products, "is_mobile": False}, request)
#             html_mobile = render_to_string("store/admin_partials/admin_product_list_mobile.html", {"products": products, "is_mobile": True}, request)

#             print(f"DEBUG: AJAX Response - Desktop HTML: {len(html_desktop)} chars, Mobile HTML: {len(html_mobile)} chars")

#             return JsonResponse({"html_desktop": html_desktop, "html_mobile": html_mobile})

#         # Add additional keys to the context for approved sellers
#         context.update({
#             'products': products,
#             'query': query,
#             'categories': all_categories,
#             'selected_filters': {
#                 'category': category,
#                 'min_price': min_price,
#                 'max_price': max_price,
#                 'status': status,
#                 'stock_status': stock_status,
#                 'sort_by': sort_by
#             }
#         })

#         print("Dashboard context:", context)

#         return render(request, 'store/admin/admin_dashboard.html', context)

#     except Exception as e:
#         error_message = f"Error fetching products: {str(e)}"
#         traceback.print_exc()  # Print full error in console

#         # ✅ Return JSON response if it's an AJAX request
#         if request.headers.get("X-Requested-With") == "XMLHttpRequest":
#             return JsonResponse({"error": error_message}, status=500)

#         # Otherwise, render the HTML page with an error message
#         messages.error(request, error_message)
#         return render(request, 'store/admin/admin_dashboard.html', {'products': [], 'query': query})


@admin_required
def delete_product_view(request, product_id):
    response = delete_product(request, product_id)
    clear_products_cache()  # Clear cache after deletion
    return response


def about_us(request):
    return render(request, "store/about_us.html")


@csrf_exempt
def apply_promo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            promo_code = data.get('promo_code', '').strip()

            if not promo_code:
                return JsonResponse({'success': False, 'error': 'No promo code provided'})

            # Use the helper function to fetch promo details
            promo_details = get_promo_code_details(promo_code)

            return JsonResponse(promo_details)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def checkout(request):
    """Checkout logic to validate cart and fetch product details"""
    user_id = request.session.get("uid")

    cart_items = CartService.get_cart_summary(user_id)

    if not cart_items:
        messages.warning(request, 'Your cart is empty')
        return redirect('/')

    product_ids = [item['product_id'] for item in cart_items]
    products = get_products_by_ids(product_ids)

    validated_cart = {
        str(item['product_id']): {
            'name': product['name'],
            'price': float(product['price']),  # Convert to float
            'image_url': product['image_url'],
            'quantity': item['quantity'],
            # Convert to float
            'total_price': float(product['price'] * item['quantity']),
            'seller_name': product.get('seller_name', 'Unknown Store')
        }
        for item, product in zip(cart_items, products)
    }

    request.session['cart'] = validated_cart

    subtotal = sum(item['total_price'] for item in validated_cart.values())

    # Convert shipping and discount to floats
    # Default to 99 if not provided
    shipping = float(request.GET.get('shipping', 99))
    # Default to 0 if not provided
    discount = float(request.GET.get('discount', 0))

    total = subtotal + shipping - discount

    context = {
        'cart': validated_cart,
        'subtotal': subtotal,
        'shipping': shipping,
        'discount': discount,
        'final_total': total
    }

    return render(request, 'store/checkout.html', context)


@login_required
def place_order(request):
    if request.method == "POST":
        try:
            user_id = request.session.get("uid")
            if not user_id:
                return JsonResponse({"error": "User not authenticated"}, status=401)

            # Parse JSON data from the request body
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON format"}, status=400)

            address = data.get("address", {})
            name = address.get("name")
            mobile = address.get("mobile")
            pincode = address.get("pincode")
            house_no = address.get("house_no")
            street = address.get("street")
            city = address.get("city")
            state = address.get("state")
            country = address.get("country")

            payment_method = data.get("payment_method")

            # Extract shipping and discount values
            shipping = data.get("shipping", 0)
            discount = data.get("discount", 0)
            subtotal = data.get("subtotal", 0)
            total = data.get("total", 0)

            if not payment_method:
                return JsonResponse({"error": "Payment method is required"}, status=400)

            if not all([name, mobile, pincode, house_no, street, city, state, country]):
                return JsonResponse({"error": "All address fields are required"}, status=400)

            cart = request.session.get("cart", {})
            if not cart:
                return JsonResponse({"error": "Cart is empty"}, status=400)

            # total_price = sum(
            #     float(item["price"]) * int(item["quantity"]) for item in cart.values()
            # )

            # Use the provided total, or calculate it from cart if not provided
            if not total:
                total_price = sum(
                    float(item["price"]) * int(item["quantity"]) for item in cart.values()
                )
            else:
                total_price = total

            address_data = {
                "name": name,
                "mobile": mobile,
                "pincode": pincode,
                "house_no": house_no,
                "street": street,
                "city": city,
                "state": state,
                "country": country,
            }

            # Retrieve the admin/store from the first product in the cart.
            first_product_key = list(cart.keys())[0]
            try:
                product = Product.objects.get(id=int(first_product_key))
                # Assuming the Product model's FK is named admin_id.
                order_admin = product.admin_id
            except Exception as e:
                order_admin = None
                print("Warning: Could not retrieve admin/store for the order", e)

            # Create order
            order_id, error = create_order(
                user_id, total_price, payment_method, address_data, shipping=shipping, discount=discount, order_admin=order_admin)
            if not order_id:
                return JsonResponse({"error": "Order creation failed", "details": str(error)}, status=500)

            # Create order items
            error = create_order_items(order_id, cart)
            if error:
                delete_order(order_id)  # Rollback order
                return JsonResponse({"error": "Order items creation failed, order canceled"}, status=500)

            # # Delete purchased products
            # error = delete_purchased_products(cart)
            # if error:
            #     delete_order(order_id)  # Rollback order and items
            #     return JsonResponse({"error": "Failed to remove products, order canceled"}, status=500)

            send_admin_notification_email(
                request, order_id, user_id, address_data, total_price)

            # Store last order and clear cart
            request.session["last_order"] = {
                "cart": cart,
                "total_price": total_price,
                "shipping": shipping,
                "discount": discount
            }
            request.session["cart"] = {}

            return JsonResponse({"success": "Order placed successfully!"})

        except Exception as e:
            print("Error:", str(e))
            traceback.print_exc()
            return JsonResponse({"error": "Something went wrong"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


def send_confirmation_email(user_id, order_id, address, total_price):
    # Retrieve the user's email from Supabase
    user_email = get_user_email(user_id)

    if not user_email:
        return None  # If email could not be fetched, return None

    # Generate the confirmation email content
    subject = f"Order Confirmation - Order #{order_id}"
    message = f"Dear {address.get('name')},\n\nThank you for your order #{order_id}. " \
        f"Your order has been successfully confirmed and is being processed.\n\n" \
        f"Order Summary:\n" \
        f"Total Price: ₹{total_price}\n\n" \
        f"Shipping Address:\n{address.get('house_no')} {address.get('street')}\n" \
        f"{address.get('city')}, {address.get('state')}, {address.get('country')}, {address.get('pincode')}\n\n" \
        f"Estimated Delivery: 5-7 business days\n\n" \
        f"Contact Us for Support: support@yourstore.com"

    # Send the email to the user's email address
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])


def send_rejection_email(user_id, order_id):
    # Send email to the customer
    user_email = get_user_email(user_id)
    if not user_email:
        return None  # If user email could not be fetched, do nothing

    subject_customer = f"Order Rejected - Order #{order_id}"
    message_customer = (
        f"Dear Customer,\n\n"
        f"We regret to inform you that your order #{order_id} has been rejected by our admin. "
        f"Please feel free to contact us for further information.\n\n"
        f"Contact Us for Support: support@yourstore.com"
    )
    send_mail(subject_customer, message_customer,
              settings.DEFAULT_FROM_EMAIL, [user_email])

    # Send confirmation email to the seller (admin) who rejected the order.
    try:
        order_obj = Order.objects.get(id=order_id)
        seller_email = order_obj.admin.email if order_obj.admin and order_obj.admin.email else None
        print("Seller email for rejection confirmation:", seller_email)
    except Exception as e:
        print("Error fetching seller email:", str(e))
        seller_email = None

    if seller_email:
        subject_seller = f"Order Rejection Confirmation - Order #{order_id}"
        message_seller = (
            f"Dear {order_obj.admin.company_name},\n\n"
            f"This is a confirmation that you have rejected order #{order_id}.\n\n"
            f"Thank you for taking prompt action.\n\n"
            f"Regards,\nYour Store Team"
        )
        send_mail(subject_seller, message_seller,
                  settings.DEFAULT_FROM_EMAIL, [seller_email])


def send_admin_notification_email(request, order_id, user_id, address, total_price):
    # Retrieve admin's email from settings or environment variables
    try:
        # Retrieve the order to get the seller (admin) information.
        order_obj = Order.objects.get(id=order_id)
        # Get the admin email from the order's related AdminStore record.
        admin_email = order_obj.admin.email if order_obj.admin and order_obj.admin.email else settings.DEFAULT_FROM_EMAIL
        print("Order admin email:", admin_email)
    except Exception as e:
        print("Error fetching admin email:", str(e))
        admin_email = settings.DEFAULT_FROM_EMAIL

    # Generate action URLs
    approval_url = request.build_absolute_uri(
        reverse('admin_approve_order', kwargs={
                'order_id': order_id, 'action': 'approve'})
    )
    rejection_url = request.build_absolute_uri(
        reverse('admin_approve_order', kwargs={
                'order_id': order_id, 'action': 'reject'})
    )
    shipped_url = request.build_absolute_uri(
        reverse('admin_approve_order', kwargs={
                'order_id': order_id, 'action': 'shipped'})
    )

    # Generate email content
    subject = f"New Order Pending Approval - Order #{order_id}"
    message = f"""
    An order has been placed and is awaiting approval.

    Order ID: {order_id}
    Total Price: ₹{total_price}

    Shipping Address:
    {address.get('house_no')} {address.get('street')}
    {address.get('city')}, {address.get('state')}, {
        address.get('country')}, {address.get('pincode')}

    Click here to approve the order: {approval_url}
    Click here to reject the order: {rejection_url}

    Once approved, mark the order as shipped: {shipped_url}

    Please take action in the admin panel.
    """

    # Send email to the admin
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email])


def send_shipped_email(user_email, order_id, address, total_price):
    subject = f"Order Shipped - Order #{order_id}"

    message = f"Your order has been shipped!\n\n" \
        f"Order ID: {order_id}\n" \
        f"Total Price: ₹{total_price}\n\n" \
        f"Shipping Address:\n{address.get('house_no')} {address.get('street')}\n" \
        f"{address.get('city')}, {address.get('state')}, {address.get('country')}, {address.get('pincode')}\n\n" \
        f"Your order is now on the way. Thank you for shopping with us!"

    # Send the email to the user
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])


def admin_orders(request):
    # query = request.GET.get('q', '').strip()
    orders = get_all_orders_for_admin()

    return render(request, 'store/admin/admin_orders.html', {'orders': orders})


@admin_required
def admin_approve_order(request, order_id, action):
    if request.method != "POST":
        return HttpResponseRedirect(reverse('admin_orders'))
    try:
        # Fetch the order instance
        order = get_order_by_id(order_id)  # Returns an Order instance
        print(f"DEBUG: Order fetched -> {order} (Type: {type(order)})")

        if not order:
            return JsonResponse({"error": "Order not found"}, status=404)

        # Access address using attribute access.
        # If order.address is already a dict, no need to json.loads; otherwise, convert it.
        order_address = order.address if isinstance(
            order.address, dict) else json.loads(order.address)

        # Fetch order items (assuming get_order_items returns a list of product IDs)
        order_items = get_order_items(order_id)
        print(
            f"DEBUG: Order items -> {order_items} (Type: {type(order_items)})")

        if not order_items:
            print(f"No items found for order ID {order_id}")
            return JsonResponse({"error": f"No items found for order {order_id}"}, status=404)

        if action == "approve":
            # Update order status to confirmed.
            result = update_order_status(order_id, "confirmed")
            if result:  # Assuming True means success.
                # Delete purchased products
                # Adjust if get_order_items returns objects instead of IDs.
                product_ids = order_items
                error = delete_purchased_products(product_ids)
                if error:
                    return JsonResponse({"error": "Failed to remove purchased products."}, status=500)

                # Send confirmation email to user.
                send_confirmation_email(
                    order.user_id.id, order_id, order_address, order.total_price)
                return redirect('admin_orders')
            else:
                return JsonResponse({"error": "Failed to update order status"}, status=500)

        elif action == "reject":
            result = update_order_status(order_id, "rejected")
            if result:
                # Fetch OrderItem objects to get quantities
                order_items = OrderItem.objects.filter(order_id=order_id)

                for order_item in order_items:
                    product = order_item.product_id  # This should be a Product instance
                    product.stock += order_item.quantity  # Restore stock
                    product.is_active = True  # Ensure product is active again
                    product.save()

                send_rejection_email(order.user_id.id, order_id)
                return redirect('admin_orders')
            else:
                return JsonResponse({"error": "Failed to update order status"}, status=500)

        elif action == "shipped":
            result = update_order_status(order_id, "shipped")
            if result:
                print(f"🔍 Order User ID: {order.user_id.id}")
                if not order.user_id:
                    print("⚠️ No user ID found for this order. Skipping email sending.")
                    return redirect('admin_orders')

                user_email = get_user_email(order.user_id.id)
                print(f"🛠️ Debug: get_user_email returned: {user_email}")

                if not user_email:
                    print(
                        f"⚠️ Could not send shipping email: Invalid email for user {order.user_id.id}")
                else:
                    send_shipped_email(user_email, order_id,
                                       order_address, order.total_price)

                return redirect('admin_orders')
            else:
                return JsonResponse({"error": "Failed to update order status"}, status=500)
        else:
            return JsonResponse({"error": "Invalid action."}, status=400)

    except Exception as e:
        return JsonResponse({"error": f"Something went wrong: {str(e)}"}, status=500)


@login_required
def order_success(request):
    # Fetch the last order from the session
    last_order = request.session.get("last_order", {})

    if not last_order:
        messages.error(request, "No recent order found.")
        return redirect("home")

    try:
        # Retrieve the user instance from session
        user_id = request.session.get("uid")
        user = User.objects.get(id=user_id)

        # Fetch the user's most recent order from the database using ORM
        order_obj = Order.objects.filter(
            user_id=user).order_by("-created_at").first()

        if order_obj:
            # Build a dictionary for the order details
            recent_order = {
                "id": order_obj.id,
                "user_id": order_obj.user_id.id,
                "total_price": order_obj.total_price,
                "status": order_obj.status,
                "created_at": order_obj.created_at,
                "shipping": order_obj.shipping_rate if order_obj.shipping_rate else last_order.get("shipping", 0),
                "discount": order_obj.discount_rate if order_obj.discount_rate else last_order.get("discount", 0),
                "address": order_obj.address,  # Already a dict if JSONField is used
                "payment_method": order_obj.payment_method,
            }

            # Fetch order items for this specific order.
            # Use values() to create a list of dicts.
            order_items = list(order_obj.items.all().values(
                "id", "quantity", "price", "total_price", "created_at", "name", "product_id"
            ))

            context = {
                "order": recent_order,
                "order_items": order_items,
                "cart": last_order.get("cart", {}),
                "total_price": recent_order.get("total_price", last_order.get("total_price", 0)),
            }

            # Clear the last order from session
            if "last_order" in request.session:
                del request.session["last_order"]
                request.session.modified = True

            return render(request, "store/order_success.html", context)
        else:
            messages.error(request, "Unable to retrieve order details.")
            return redirect("home")

    except Exception as e:
        print(f"Error fetching order details: {e}")
        messages.error(
            request, "An error occurred while retrieving order details.")
        return redirect("home")


def order_details(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        items = OrderItem.objects.filter(order_id=order).select_related(
            'product_id')  # Corrected filter
        items_data = [
            {
                "product_id": item.product_id.id,  # Return the product's ID as a primitive value
                "product_name": item.product_id.name,
                "quantity": item.quantity,
                "price": item.price,
                "product_rate": item.product_id.price
            }
            for item in items
        ]
        # Example calculation
        selling_price = sum(float(item.price) *
                            item.quantity for item in items)
        response_data = {
            "items": items_data,
            "discount_rate": order.discount_rate,
            "shipping_rate": order.shipping_rate,
            "order_total": order.total_price,
            "selling_price": selling_price  # Add if using Option 1
        }
        return JsonResponse(response_data)
    except Order.DoesNotExist:
        logger.error(f"Order with ID {order_id} not found.")
        return JsonResponse({"error": "Order not found"}, status=404)
    except Exception as e:
        logger.exception("Unexpected error in order_details view:")
        return JsonResponse({"error": "Unexpected error"}, status=500)


def admin_analysis(request):
    return render(request, "store/admin/admin_analysis.html")


@login_required
def orders_view(request):
    user_id = request.session.get('uid')

    if not user_id:
        return redirect('login')

    orders_data = get_user_orders(user_id)  # Fetch orders using the service
    total_orders = len(orders_data)
    shipped_orders = sum(
        1 for order in orders_data if order["status"].lower() == "shipped")
    processing_orders = sum(
        1 for order in orders_data if order["status"].lower() == "confirmed")
    delivered_orders = sum(
        1 for order in orders_data if order["status"].lower() == "delivered")
    rejected_orders = sum(1 for order in orders_data if order["status"].lower() in [
                          "rejected"])
    cancelled_orders = sum(
        1 for order in orders_data if order["status"].lower() == "canceled")

    context = {
        "orders": orders_data,
        "total_orders": total_orders,
        "shipped_orders": shipped_orders,
        "processing_orders": processing_orders,
        "delivered_orders": delivered_orders,
        "rejected_orders": rejected_orders,
        "cancelled_orders": cancelled_orders,
    }
    return render(request, "store/orders.html", context)


@login_required
def cancel_order(request, order_id):
    # Retrieve the order ensuring it belongs to the logged-in user
    order = get_object_or_404(
        Order, id=order_id, user_id=request.session.get("uid"))

    # Check if order is in a cancelable state: "confirmed" or "pending"
    if order.status.lower() not in ["confirmed", "pending"]:
        messages.error(
            request, "This order cannot be cancelled at this stage.")
        # Replace with the appropriate orders view name
        return redirect("orders")

    # Restore stock for each product in the order
    order_items = OrderItem.objects.filter(order_id=order)  # Fixed field name
    for order_item in order_items:
        product = order_item.product_id  # This should be a Product instance
        product.stock += order_item.quantity  # Restore stock
        product.is_active = True  # Ensure the product is marked as active again
        product.save()

    # Update the order status to "canceled"
    order.status = "canceled"
    order.save()

    # Send cancellation emails to both the user and admin
    send_cancellation_email(request.session.get("uid"), order.id)

    messages.success(request, "Your order has been successfully cancelled.")
    return redirect("orders")


def send_cancellation_email(user_id, order_id):
    # Retrieve the customer's email.
    user_email = get_user_email(user_id)

    # Retrieve the main admin email from settings.
    main_admin_email = getattr(settings, "ADMIN_EMAIL", None)

    # Retrieve the seller's (order's admin) email.
    seller_admin_email = None
    try:
        order_obj = Order.objects.get(id=order_id)
        seller_admin_email = order_obj.admin.email if order_obj.admin and order_obj.admin.email else None
        print("Order seller admin email:", seller_admin_email)
    except Exception as e:
        print("Error fetching order admin email:", str(e))

    if not user_email:
        return None  # If user email is not available, do nothing.

    # Email to the customer.
    subject_user = f"Order Cancellation - Order #{order_id}"
    message_user = (
        f"Dear Customer,\n\n"
        f"Your order #{order_id} has been cancelled as per your request. "
        f"If you have any questions, please contact our support team at support@yourstore.com.\n\n"
        f"Best Regards,\nYour Store Team"
    )
    send_mail(subject_user, message_user,
              settings.DEFAULT_FROM_EMAIL, [user_email])

    # Build list of admin recipients: include main admin and seller's email.
    admin_recipients = []
    if main_admin_email:
        admin_recipients.append(main_admin_email)
    if seller_admin_email and seller_admin_email not in admin_recipients:
        admin_recipients.append(seller_admin_email)

    # Email to the admins.
    if admin_recipients:
        subject_admin = f"Order Cancellation Notification - Order #{order_id}"
        message_admin = (
            f"Dear Admin,\n\n"
            f"Order #{order_id} has been cancelled by the customer. "
            f"Please review the order details and process any further actions if needed.\n\n"
            f"Regards,\nYour Store System"
        )
        send_mail(subject_admin, message_admin,
                  settings.DEFAULT_FROM_EMAIL, admin_recipients)


def help_support(request):
    return render(request, 'store/help_support.html')


@require_POST
def update_stock(request):
    try:
        product_id = int(request.POST.get('product_id'))
        new_stock = int(request.POST.get('new_stock'))

        product = Product.objects.get(id=product_id)

        # Update stock
        product.stock = new_stock

        # Ensure is_active is True when stock is available
        product.is_active = new_stock > 0

        product.save()

        # Refresh from the database to ensure changes are reflected
        product.refresh_from_db()

        print(
            f"✅ Product {product_id} updated: Stock = {product.stock}, is_active = {product.is_active}")

        # Replace with actual dashboard URL name
        return redirect("admin_dashboard")

    except (Product.DoesNotExist, ValueError, TypeError) as e:
        print(f"❌ Error updating stock: {str(e)}")
        return JsonResponse({'success': False})


@csrf_exempt
def admin_signup(request):
    if request.method == "GET":
        return render(request, "store/admin/admin_signup.html")
    if request.method == 'POST':
        uid = request.POST.get("uid")
        company_name = request.POST.get("company_name")
        shop_address = request.POST.get("shop_address")
        pincode = request.POST.get("pincode")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        company_logo = request.FILES.get("company_logo")

        # Validate that all fields are provided
        if not all([uid, company_name, shop_address, pincode, phone, email]):
            return JsonResponse({"success": False, "error": "All fields are required."})

        # Create a new AdminStore record
        try:
            # Use the separate ORM function to create a new AdminStore record
            admin_record = create_admin_store_record(
                uid, company_logo, company_name, email, phone, shop_address, pincode
            )

            # Send an email to notify the superadmin about the new pending signup.
            # Either use a hardcoded email or use a value from settings.
            SUPERADMIN_EMAIL = getattr(
                settings, "SUPERADMIN_EMAIL", "farazashraf413@gmail.com")
            subject = "New Admin Signup Pending Approval"
            message = (
                f"A new admin signup has been submitted.\n\n"
                f"Company Name: {company_name}\n"
                f"Email: {email}\n"
                f"Phone: {phone}\n\n"
                "Please review the signup in the Django admin panel and approve if valid."
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                      [SUPERADMIN_EMAIL])

            # Return a JSON response indicating the signup is pending approval.
            return JsonResponse({"success": True, "message": "Your signup is pending approval. Please wait."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    else:
        return JsonResponse({"success": False, "error": "Invalid request method."})


def seller_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = AdminStore.objects.filter(email=email, is_approved=True).first()
        if user:
            request.session["is_seller"] = True
            request.session["seller_id"] = str(user.id)
            return redirect("seller_dashboard")
        else:
            messages.error(request, "You are not approved yet.")
    return render(request, "seller_login.html")

# def super_admin(request):
#     if request.method == "POST":
#         email = request.POST.get("email")
#         password = request.POST.get("password")
#         user = authenticate(request, username=email, password=password)
#         if user is not None:
#             # Check if the user is the designated superadmin
#             if user.email == SUPERADMIN_EMAIL:
#                 login(request, user)
#                 return redirect(reverse("super_admin"))
#             else:
#                 messages.error(request, "You are not authorized to access the superadmin dashboard.")
#         else:
#             messages.error(request, "Invalid email or password.")
#     return render(request, "store/admin/super_admin.html")

# Helper to restrict access to superadmins.


def superadmin_required(user):
    return user.is_superuser


@login_required
@user_passes_test(superadmin_required)
def approve_admin_signup(request, seller_id):
    seller = get_object_or_404(AdminStore, id=seller_id)
    if request.method == "POST":
        seller.is_approved = True
        seller.save()

        # Retrieve seller email from the AdminStore record
        seller_email = seller.email

        subject = "Your Seller Account Has Been Approved"
        message = (
            f"Congratulations!\n\nYour seller account for {seller.company_name} has been approved. "
            "You can now log in and start selling on our platform."
        )
        send_mail(subject, message,
                  settings.DEFAULT_FROM_EMAIL, [seller_email])

        messages.success(request, "Seller approved and notified via email.")

        request.session["approval_message"] = "Approved by the ADMIN"
        # Redirect to a page listing pending signups.
        return redirect("pending_seller_signups")
    else:
        # Optionally, render a confirmation page.
        return render(request, "store/admin/admin_dashboard.html", {"seller": seller})


def seller_page(request):
    """
    View to fetch and display all approved sellers.
    """
    # Fetch all approved sellers ordered by company name
    sellers = AdminStore.objects.filter(
        is_approved=True).order_by('company_name')
    logger.debug(f"Sellers count: {sellers.count()}")

    # Generate public URLs for company logos
    for seller in sellers:
        if seller.company_logo:
            try:
                seller.company_logo = supabase.storage.from_(
                    "product-image").get_public_url(seller.company_logo)
                logger.debug(f"Company logo public URL: {seller.company_logo}")
            except Exception as e:
                logger.error(
                    f"Error generating public URL for company logo: {e}")
                seller.company_logo = static('images/placeholder.png')
        else:
            seller.company_logo = static('images/placeholder.png')

    context = {
        'sellers': sellers,
    }
    return render(request, 'store/seller.html', context)


def seller_details(request, adminstore_id):
    """
    View to fetch a single seller's details along with their products.
    Uses the AdminStore's id (UUID) to look up the seller.
    """
    # Get the seller by AdminStore id or return a 404 if not found.
    seller = get_object_or_404(AdminStore, id=adminstore_id)

    # Generate public URL for the company logo
    if seller.company_logo:
        try:
            # Assuming company logos are stored in the same bucket as product images
            seller.company_logo_url = supabase.storage.from_(
                "product-image").get_public_url(seller.company_logo)
            logger.debug(f"Company logo public URL: {seller.company_logo_url}")
        except Exception as e:
            logger.error(f"Error generating public URL for company logo: {e}")
            seller.company_logo_url = static('images/placeholder.png')
    else:
        seller.company_logo_url = static('images/placeholder.png')

    # Fetch products that belong to this seller, are active and not deleted
    products = seller.products.filter(
        is_active=True, is_deleted=False).order_by('-created_at')

    # Generate public URLs for product images
    for product in products:
        if product.image_url:
            try:
                product.main_image_url = supabase.storage.from_(
                    "product-image").get_public_url(product.image_url)
                logger.debug(f"Product image URL: {product.main_image_url}")
            except Exception as e:
                logger.error(
                    f"Error generating public URL for product image: {e}")
                product.main_image_url = static('images/placeholder.png')
        else:
            product.main_image_url = static('images/placeholder.png')

    context = {
        'seller': seller,
        'products': products,
    }

    # Remove the duplicate return statement
    return render(request, "store/seller_details.html", context)


def seller_product_details(request, product_id):
    """
    View to fetch a single product's details and return its public image URLs.
    Always fetch the main image (image_url). If it's not available, optionally use
    the first additional image as fallback.
    """
    product = get_object_or_404(Product, id=product_id)

    images = []
    # Always attempt to fetch the main image (image_url)
    if product.image_url:
        main_url = supabase.storage.from_(
            "product-image").get_public_url(product.image_url)
        logger.debug(f"Main image public URL: {main_url}")
        images.append(main_url)
    else:
        # Optionally: fallback to first additional image if main is missing.
        if product.image_url2:
            main_url = supabase.storage.from_(
                "product-image").get_public_url(product.image_url2)
            logger.debug(f"Fallback main image from image_url2: {main_url}")
            images.append(main_url)

    # Fetch additional images if they exist; avoid duplicate if already added.
    if product.image_url2:
        url2 = supabase.storage.from_(
            "product-image").get_public_url(product.image_url2)
        if url2 not in images:
            logger.debug(f"Additional image 2 URL: {url2}")
            images.append(url2)
    if product.image_url3:
        url3 = supabase.storage.from_(
            "product-image").get_public_url(product.image_url3)
        logger.debug(f"Additional image 3 URL: {url3}")
        images.append(url3)
    if product.image_url4:
        url4 = supabase.storage.from_(
            "product-image").get_public_url(product.image_url4)
        logger.debug(f"Additional image 4 URL: {url4}")
        images.append(url4)

    # If no images were found, use a default placeholder image.
    if not images:
        # Ensure this static file exists.
        placeholder = "{% static 'images/placeholder.png' %}"
        logger.debug("No images found; using placeholder.")
        images.append(placeholder)

    context = {
        'product': product,
        # List of public URLs for each image field that exists.
        'images': images,
    }
    return render(request, 'store/product_detail.html', context)


def seller_order_analytics(request):
    """
    Returns analytics data for the currently logged-in seller.
    """
    # Get the admin UID from the session (set when the admin logs in)
    admin_uid = request.session.get('admin_uid')
    if not admin_uid:
        return JsonResponse({"error": "Admin not authenticated"}, status=401)

    try:
        # Fetch the AdminStore instance from the database
        admin_store = AdminStore.objects.get(firebase_uid=admin_uid)
    except AdminStore.DoesNotExist:
        return JsonResponse({"error": "Admin store not found"}, status=404)

    # Filter orders and order items by the retrieved admin_store
    orders = Order.objects.filter(admin=admin_store)
    total_orders = orders.count()

    revenue_data = orders.aggregate(total_revenue=Sum('total_price'))
    total_revenue = revenue_data.get('total_revenue') or 0

    avg_order_value = orders.aggregate(
        avg_value=Avg('total_price')).get('avg_value') or 0

    items_data = OrderItem.objects.filter(
        admin=admin_store).aggregate(total_items=Sum('quantity'))
    total_items_sold = items_data.get('total_items') or 0

    orders_by_status = orders.values('status').annotate(count=Count('id'))

    top_products = OrderItem.objects.filter(admin=admin_store).values('product_id__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_quantity')[:5]

    data = {
        'total_orders': total_orders,
        'total_revenue': float(total_revenue),
        'avg_order_value': float(avg_order_value),
        'total_items_sold': total_items_sold,
        # e.g. [{'status': 'pending', 'count': 10}, ...]
        'orders_by_status': list(orders_by_status),
        # e.g. [{'product_id__name': 'T-shirt', 'total_quantity': 25, 'total_revenue': 1500}, ...]
        'top_products': list(top_products),
    }
    return JsonResponse(data)


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
        return render(request, "store/admin/admin_login.html")

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        id_token = data.get("token")

        if not id_token:
            logger.warning("❌ No token provided in request")
            return JsonResponse({"error": "No token provided"}, status=400)

        logger.info(f"🔑 Received Firebase ID Token: {id_token[:50]}...")

        # Verify Firebase ID token
        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")
            logger.info(
                f"✅ Firebase authentication successful: {email} ({uid})")
        except auth.ExpiredIdTokenError:
            logger.error("❌ Expired Firebase ID token")
            return JsonResponse({"error": "Expired token"}, status=401)
        except auth.InvalidIdTokenError:
            logger.error("❌ Invalid Firebase ID token")
            return JsonResponse({"error": "Invalid token"}, status=401)
        except Exception as e:
            logger.error(f"❌ Firebase Auth error: {str(e)}")
            return JsonResponse({"error": "Authentication failed"}, status=401)

        # Look up the admin user by email from your AdminStore model
        try:
            admin_user = AdminStore.objects.get(email=email)
        except AdminStore.DoesNotExist:
            logger.warning(f"❌ No admin account found for {email}")
            return JsonResponse({"error": "Unauthorized access"}, status=403)

        # # Check if the seller's account is approved
        # if not admin_user.is_approved:
        #     logger.warning(f"❌ Admin account for {email} is pending approval")
        #     return JsonResponse({"error": "Your account is pending approval. Please wait for an admin to approve your account."}, status=403)

        # If approved, set the session and allow access
        request.session["admin_authenticated"] = True
        request.session["admin_uid"] = uid
        request.session["admin_email"] = email
        return JsonResponse({"success": True, "redirect": "/store-admin/dashboard/"})

    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON format in request body")
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        logger.error(f"❌ Unexpected error in admin_login: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


def admin_dashboard(request, admin_id=None):
    """
    View function for the admin dashboard of VendorHub
    """
    # Check for the current admin/store
    try:
        if admin_id:
            admin = AdminStore.objects.get(id=admin_id)
        else:
            admin_email = request.session.get(
                "admin_email")  # Get email from session
            if not admin_email:
                messages.error(request, "No admin email found. Please log in.")
                # Redirect to login if no email in session
                return redirect(reverse('admin_login'))

            admin = AdminStore.objects.get(
                email=admin_email)  # Fetch using session email
    except AdminStore.DoesNotExist:
        messages.error(
            request, "Admin account not found. Please sign up as an admin.")
        return redirect(reverse('admin_signup'))  # Redirect if admin not found

    # Get the public URL for the main image if it exists
    company_logo_url = (
        supabase.storage.from_(
            "product-image").get_public_url(admin.company_logo)
        if admin.company_logo
        else None
    )
    print("Company logo URL:", company_logo_url)

    # Get today's date
    today = timezone.now().date()
    yesterday = today - datetime.timedelta(days=1)

    # Get today's sales
    today_sales = Order.objects.filter(
        admin=admin,
        created_at__date=today
    ).aggregate(
        total=Sum('total_price', default=0)
    )['total'] or 0

    # Get yesterday's sales for comparison
    yesterday_sales = Order.objects.filter(
        admin=admin,
        created_at__date=yesterday
    ).aggregate(
        total=Sum('total_price', default=0)
    )['total'] or 0

    # Calculate percentage change
    if yesterday_sales > 0:
        sales_percentage = (
            (today_sales - yesterday_sales) / yesterday_sales) * 100
    else:
        sales_percentage = 100 if today_sales > 0 else 0

    # Get pending orders
    pending_orders = Order.objects.filter(
        admin=admin,
        status='pending'
    ).count()

    # Get orders that need attention (you can define what needs attention)
    # For example, orders that have been pending for more than 24 hours
    attention_needed = Order.objects.filter(
        admin=admin,
        status='pending',
        created_at__lt=timezone.now() - datetime.timedelta(hours=24)
    ).count()

    # Get current month's earnings
    first_day_of_month = today.replace(day=1)
    monthly_earnings = Order.objects.filter(
        admin=admin,
        created_at__date__gte=first_day_of_month,
        created_at__date__lte=today
    ).exclude(status__in=['rejected', 'pending', 'canceled']).aggregate(
        total=Sum('total_price', default=0)
    )['total'] or 0

    # Calculate store visitors (this would typically come from analytics)
    # In a real app, you might integrate with Google Analytics or similar
    # For demonstration, we'll use a placeholder based on orders
    week_ago = today - datetime.timedelta(days=7)
    current_week_orders = Order.objects.filter(
        admin=admin,
        created_at__date__gte=week_ago
    ).count()

    previous_week_orders = Order.objects.filter(
        admin=admin,
        created_at__date__gte=week_ago - datetime.timedelta(days=7),
        created_at__date__lt=week_ago
    ).count()

    # Simulate visitor count based on orders
    visitors = current_week_orders * 50  # assumption: 50 visitors per order

    if previous_week_orders > 0:
        visitors_percentage = (
            (current_week_orders - previous_week_orders) / previous_week_orders) * 100
    else:
        visitors_percentage = 100 if current_week_orders > 0 else 0

    # Get recent orders
    recent_orders = Order.objects.filter(
        admin=admin
    ).order_by('-created_at')[:5]

    # Format recent orders for display
    recent_orders_display = []
    for order in recent_orders:
        items_count = OrderItem.objects.filter(order_id=order).count()
        status_class = "green" if order.status == "delivered" else "yellow"

        recent_orders_display.append({
            'order_number': f"#ORD-{order.id}",
            'items_count': items_count,
            'total_price': order.total_price,
            'status': order.status.capitalize(),
            'status_class': status_class
        })

    # Get products with low stock
    low_stock_products = Product.objects.filter(
        admin_id=admin,
        is_active=True,
        is_deleted=False,
        stock__lte=5
    ).order_by('id').distinct('id')[:5]

    # Debug: print product IDs
    print("Low stock product IDs:")
    for p in low_stock_products:
        print(p.id)

    # Format low stock products for display
    low_stock_display = []
    for product in low_stock_products:
        low_stock_display.append({
            'id': product.id,
            'name': product.name,
            'stock': product.stock
        })

    context = {
        'admin': admin,
        'company_logo': company_logo_url,
        'today_sales': today_sales,
        'sales_percentage': round(sales_percentage, 1),
        'pending_orders': pending_orders,
        'attention_needed': attention_needed,
        'monthly_earnings': monthly_earnings,
        'visitors': visitors,
        'visitors_percentage': round(visitors_percentage, 1),
        'recent_orders': recent_orders_display,
        'low_stock_products': low_stock_display,
        'active_page': 'dashboard',
        # Add announcements - in a real app, these might come from a database
        'announcements': [
            {
                'icon': 'bullhorn',
                'icon_class': 'blue-400',
                'title': 'New Feature Release',
                'message': 'Check out our new inventory management system launching next week!'
            },
            {
                'icon': 'clock',
                'icon_class': 'yellow-400',
                'title': 'Upcoming Maintenance',
                'message': f'System maintenance scheduled for {(today + datetime.timedelta(days=7)).strftime("%B %d, %Y")} at 2:00 AM EST'
            }
        ]
    }

    return render(request, 'store/admin/admin_dashboard.html', context)


def admin_orders(request):
    # query = request.GET.get('q', '').strip()
    orders = get_all_orders_for_admin()

    context = {
        'active_page': 'orders',
        'orders': orders
    }

    return render(request, 'store/admin/admin_orders.html', context)


def order_details(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        items = OrderItem.objects.filter(order_id=order).select_related(
            'product_id')  # Corrected filter
        items_data = [
            {
                "product_id": item.product_id.id,  # Return the product's ID as a primitive value
                "product_name": item.product_id.name,
                "quantity": item.quantity,
                "price": item.price,
                "product_rate": item.product_id.price
            }
            for item in items
        ]
        # Example calculation
        selling_price = sum(float(item.price) *
                            item.quantity for item in items)
        response_data = {
            "items": items_data,
            "discount_rate": order.discount_rate,
            "shipping_rate": order.shipping_rate,
            "order_total": order.total_price,
            "selling_price": selling_price  # Add if using Option 1
        }
        return JsonResponse(response_data)
    except Order.DoesNotExist:
        logger.error(f"Order with ID {order_id} not found.")
        return JsonResponse({"error": "Order not found"}, status=404)
    except Exception as e:
        logger.exception("Unexpected error in order_details view:")
        return JsonResponse({"error": "Unexpected error"}, status=500)


@require_POST
@admin_required
def restock_product(request):
    """
    Processes a restock request from the admin dashboard.
    Expects a POST with 'product_id' and 'quantity' and updates only that product.
    """
    product_id = request.POST.get('product_id')
    quantity_value = request.POST.get('quantity')

    try:
        quantity = int(quantity_value)
    except (ValueError, TypeError):
        messages.error(request, "Invalid quantity provided.")
        return redirect(reverse('admin_dashboard'))

    if quantity <= 0:
        messages.error(request, "Quantity must be greater than zero.")
        return redirect(reverse('admin_dashboard'))

    # Debug: log the received product id and quantity
    print("Restocking product_id:", product_id, "by quantity:", quantity)

    # Retrieve the specific product based on the product_id
    product = get_object_or_404(Product, id=product_id)
    original_stock = product.stock
    product.stock += quantity
    product.save()

    messages.success(
        request, f"Successfully restocked {product.name} from {original_stock} to {product.stock} units.")
    return redirect(reverse('admin_dashboard'))


def clear_products_cache():
    cache.delete("all_products_with_variants")


@admin_required
@csrf_exempt
def add_product_view(request):
    if request.method == 'GET':
        return render(request, 'store/admin/add_product.html')

    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        price = float(request.POST.get('price'))
        original_price = float(request.POST.get('originalprice'))
        description = request.POST.get('description')
        sizes = request.POST.get('sizes', '')
        fit = request.POST.get('fit', '')
        stock = request.POST.get('stock')

        # Get the main image and additional images (as a list)
        image = request.FILES.get('image')
        additional_images = request.FILES.getlist('additional_images')

        # Validate required fields
        if not all([name, category_id, subcategory_id, price, original_price, description]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # # Check if category and subcategory exist and are related
        # category = get_object_or_404(Category, id=category_id)
        # subcategory = get_object_or_404(Subcategory, id=subcategory_id, category=category)

        firebase_uid = request.session.get(
            'admin_uid')  # This is the Firebase UID
        print(f"🔹 Firebase UID from session: {firebase_uid}")

        if not firebase_uid:
            return JsonResponse({"error": "Admin is not authenticated."}, status=400)

        try:
            # Fetch the AdminStore record using Firebase UID
            admin_store = AdminStore.objects.get(firebase_uid=firebase_uid)
            admin_store_id = str(admin_store.id)  # Convert UUID to string
            print(f"🔹 Resolved AdminStore ID: {admin_store_id}")

            # Correctly ordered parameters when calling orm_add_product:
            product = orm_add_product(
                name,
                category_id,
                subcategory_id,
                price,
                original_price,
                description,
                sizes,  # This maps to the `size` field in your function
                fit,
                image,
                additional_images,
                admin_store_id,
                stock,
                request
            )

            if isinstance(product, dict) and not product.get("success"):
                # Return the error message properly
                return JsonResponse(product, status=400)
            if product:
                # Invalidate the cache after a successful product addition.
                clear_products_cache()

                messages.success(request, "Product added successfully!")
                return JsonResponse({"success": True}, status=200)
            else:
                return JsonResponse({"error": "Failed to add product."}, status=500)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def update_product_view(request, product_id):
    product_details = fetch_product_details_orm(product_id)
    if "error" in product_details:
        messages.error(request, product_details["error"])
        return JsonResponse({"error": product_details["error"]}, status=404)

    if request.method == "POST":
        name = request.POST.get("name")
        category = request.POST.get("category")
        subcategory = request.POST.get("subcategory")
        price = request.POST.get("price")
        original_price = request.POST.get("originalprice")
        description = request.POST.get("description")
        sizes = request.POST.get("sizes")
        fit = request.POST.get("fit")
        stock = request.POST.get("stock")
        image_file = request.FILES.get("image")

        additional_images_files = []
        for key, file in request.FILES.items():
            if key.startswith("additional_image_"):
                try:
                    index_part = key.split('_')[-1]
                    if index_part.isdigit():
                        additional_images_files.append((int(index_part), file))
                except (ValueError, IndexError):
                    continue
        additional_images_files = [file for _,
                                   file in sorted(additional_images_files)]

        # Update product details
        update_response = orm_update_product(
            product_id,
            name=name,
            category=category,
            subcategory=subcategory,
            price=price,
            original_price=original_price,
            description=description,
            sizes=sizes,
            fit=fit,
            stock=stock,
            image_file=image_file,
            additional_images=additional_images_files
        )

        if "error" in update_response:
            messages.error(request, update_response["error"])
            return JsonResponse({"error": update_response["error"]}, status=400)
        else:
            clear_products_cache()
            messages.success(request, "Product updated successfully!")
            return JsonResponse({"success": "Product updated successfully!"}, status=200)

    return render(request, "store/admin/admin_update_product.html", {"product": product_details})


# API endpoint to get all active categories
@require_http_methods(["GET"])
def get_categories(request):
    categories = Category.objects.filter(is_active=True).values('id', 'name')
    return JsonResponse(list(categories), safe=False)

# API endpoint to get subcategories for a specific category


@require_http_methods(["GET"])
def get_subcategories(request, category_id):
    subcategories = Subcategory.objects.filter(
        category_id=category_id,
        is_active=True
    ).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)


def admin_products(request):
    products = Product.objects.prefetch_related('variants').all()

    context = {
        'products': products,
        'active_page': 'products',  # This marks "Products" as active
        # include other context variables as needed
    }

    return render(request, 'store/admin/admin_products.html', context)


def toggle_product_status(request, product_id):
    # Only allow POST requests (or check permissions as needed)
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save()
    status = "activated" if product.is_active else "deactivated"
    messages.success(
        request, f"Product '{product.name}' has been {status}.", extra_tags='product_messages')
    return redirect('admin_products')


@admin_required
def delete_product_view(request, product_id):
    response = delete_product(request, product_id)
    clear_products_cache()  # Clear cache after deletion
    messages.success(request, "Product deleted successfully",
                     extra_tags='product_messages')
    return response


def admin_logout(request):
    """
    Logs out the admin user by clearing the session and redirects to the admin login page.
    """
    # Remove admin session keys safely
    request.session.pop("admin_authenticated", None)
    request.session.pop("admin_uid", None)
    request.session.pop("admin_email", None)

    # Optionally, you can clear the entire session:
    # request.session.flush()

    messages.success(request, "You have been logged out successfully.")
    return redirect(reverse("admin_login"))
