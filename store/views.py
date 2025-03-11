from django.shortcuts import render, redirect, get_object_or_404
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

import traceback
# Ensure your Order model is correctly imported
from store.models import Order, Product, User, Cart, OrderItem, AdminStore
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
            messages.error(request, "Seller account not found. Please sign up as a seller.")
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
    
    
    # Fetch all products
    products = get_all_products()
    
    """Display products based on category or search query"""
    category = request.GET.get("category", "").strip().lower()

    
    if category:  # Only filter if a category is explicitly selected
        products = [p for p in products if p.get("category", "").lower() == category]
        
    # Search query across all relevant fields with fuzzy matching
    query = request.GET.get("q", "").strip()
    if query:
        query = query.lower()
        products = [
            p for p in products if any(
                fuzzy_search(query, str(p[field]).lower())
                for field in [
                    "name", "category", "description", "price", "original_price", "created_at",
                    "image_url", "image_url2", "image_url3", "image_url4"
                ] if p.get(field)
            )
        ]
        
     # Retrieve sort option from the query parameters, default to 'featured'
    sort_option = request.GET.get("sort", "featured")
    
    # Sort the products list based on the sort_option
    if sort_option == "price-low":
        products.sort(key=lambda p: p.get("price", 0))
    elif sort_option == "price-high":
        products.sort(key=lambda p: p.get("price", 0), reverse=True)
    elif sort_option == "newest":
        # Assuming 'created_at' is in a sortable format (e.g., ISO date string or datetime object)
        products.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    # Otherwise, 'featured' or any other default ordering can be handled here
        

    return render(
        request,
        "store/home.html",
        {
            "products": products,
            "user_name": user_name,
            "user_email": user_email,
            "selected_category": category,
            "query": query,
            'sort_option': sort_option  
        }
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
                    'quantity': item['quantity']
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
            logger.info(f"✅ Firebase authentication successful: {email} ({uid})")
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



@admin_required
@csrf_exempt
def add_product_view(request):
    if request.method == 'GET':
        return render(request, 'store/admin/add_product.html')

    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get("category")
        price = float(request.POST.get('price'))
        originalPrice = float(request.POST.get('originalprice'))
        description = request.POST.get('description')

        # Get the main image and additional images (as a list)
        image = request.FILES.get('image')
        additional_images = request.FILES.getlist('additional_images')

        admin_id = request.session.get('admin_uid')
        print(f"🔹 Admin ID from session: {admin_id}")

        if not admin_id:
            return JsonResponse({"error": "Admin ID is missing."}, status=400)

        try:
            # Use the Django ORM function to add the product
            product = orm_add_product(
                name, category, price, originalPrice, description,
                image, additional_images, admin_id
            )
            print(f"🔹 ORM Inserted Product: {product}")
            if product:
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
        price = request.POST.get("price")
        originalPrice = request.POST.get("originalprice")
        description = request.POST.get("description")
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
            price=price,
            original_price=originalPrice,
            description=description,
            image_file=image_file,
            additional_images=additional_images_files
        )

        if "error" in update_response:
            messages.error(request, update_response["error"])
            return JsonResponse({"error": update_response["error"]}, status=400)
        else:
            messages.success(request, "Product updated successfully!")
            return JsonResponse({"success": "Product updated successfully!"}, status=200)

    return render(request, "store/admin/admin_update_product.html", {"product": product_details})



@admin_required
def admin_dashboard(request):
    email = request.session.get("admin_email")
    if not email:
        messages.error(request, "No email found for your account. Please sign up as a seller.")
        return redirect("admin_signup")
    
    try:
        seller = AdminStore.objects.get(email=email)
        print("Seller approval status:", seller.is_approved)
    except AdminStore.DoesNotExist:
        messages.error(request, "Seller account not found. Please sign up as a seller.")
        return redirect("admin_signup")
    
    # Build a basic context that always includes the seller.
    context = {'seller': seller}
    
    if not seller.is_approved:
        context = {"message": "Your account is pending approval. Please wait for an admin to approve your account."}
        return render(request, "store/admin/admin_dashboard.html", context)
    
    # If seller is approved, check for an approval message in the session.
    approval_message = request.session.get("approval_message")
    if approval_message:
        context["approval_message"] = approval_message
        # Remove the message so it only shows once.
        del request.session["approval_message"]
        
    try:
        query = request.GET.get('q', '').strip()
        category = request.GET.get('category', '')
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        status = request.GET.get('status', '')
        stock_status = request.GET.get('stock_status', '')
        
        products = fetch_all_products()  # Fetch all products from Supabase
        
        if query:
            query = query.lower()
            products = [
                p for p in products if any(
                    fuzzy_search(query, str(p[field]).lower())
                    for field in ["id", "name", "category", "description"] if p.get(field)
                )
            ]
        
        # Filter by category
        if category:
            products = [p for p in products if p.get('category') == category]
            
        # Filter by price range
        if min_price and min_price.isdigit():
            products = [p for p in products if float(p.get('price', 0)) >= float(min_price)]
            
        if max_price and max_price.isdigit():
            products = [p for p in products if float(p.get('price', 0)) <= float(max_price)]
            
        # Filter by availability status
        if status:
            if status == 'available':
                products = [p for p in products if p.get('is_active', False)]
            elif status == 'sold':
                products = [p for p in products if not p.get('is_active', True)]
                
        # Filter by stock level
        if stock_status:
            if stock_status == 'low':
                products = [p for p in products if int(p.get('stock', 0)) <= 10]
            elif stock_status == 'out':
                products = [p for p in products if int(p.get('stock', 0)) == 0]
            elif stock_status == 'in':
                products = [p for p in products if int(p.get('stock', 0)) > 10]
            
        # Get unique categories for filter dropdown
        all_categories = sorted(set(p.get('category') for p in fetch_all_products() if p.get('category')))
        
        # Existing filter code...
        sort_by = request.GET.get('sort_by', 'id_asc')
        
        # Apply sorting after all filters
        if sort_by:
            if sort_by == 'id_asc':
                products = sorted(products, key=lambda p: int(p.get('id', 0)))
            elif sort_by == 'id_desc':
                products = sorted(products, key=lambda p: int(p.get('id', 0)), reverse=True)
            elif sort_by == 'price_asc':
                products = sorted(products, key=lambda p: float(p.get('price', 0)))
            elif sort_by == 'price_desc':
                products = sorted(products, key=lambda p: float(p.get('price', 0)), reverse=True)
            elif sort_by == 'stock_asc':
                products = sorted(products, key=lambda p: int(p.get('stock', 0)))
            elif sort_by == 'stock_desc':
                products = sorted(products, key=lambda p: int(p.get('stock', 0)), reverse=True)
            
        # ✅ If AJAX request, return both `#productListDesktop` and `#productListMobile` content
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            html_desktop = render_to_string("store/admin_partials/admin_product_list_desktop.html", {"products": products, "is_mobile": False}, request)
            html_mobile = render_to_string("store/admin_partials/admin_product_list_mobile.html", {"products": products, "is_mobile": True}, request)

            print(f"DEBUG: AJAX Response - Desktop HTML: {len(html_desktop)} chars, Mobile HTML: {len(html_mobile)} chars")

            return JsonResponse({"html_desktop": html_desktop, "html_mobile": html_mobile})
        
        # Add additional keys to the context for approved sellers
        context.update({
            'products': products, 
            'query': query,
            'categories': all_categories,
            'selected_filters': {
                'category': category,
                'min_price': min_price,
                'max_price': max_price,
                'status': status,
                'stock_status': stock_status,
                'sort_by': sort_by
            }
        })
        
        print("Dashboard context:", context)

        return render(request, 'store/admin/admin_dashboard.html', context)

    except Exception as e:
        error_message = f"Error fetching products: {str(e)}"
        traceback.print_exc()  # Print full error in console

        # ✅ Return JSON response if it's an AJAX request
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": error_message}, status=500)

        # Otherwise, render the HTML page with an error message
        messages.error(request, error_message)
        return render(request, 'store/admin/admin_dashboard.html', {'products': [], 'query': query})



def delete_product_view(request, product_id):
    return delete_product(request, product_id)


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

            # Create order
            order_id, error = create_order(
                user_id, total_price, payment_method, address_data, shipping=shipping, discount=discount)
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
    user_email = get_user_email(user_id)

    if not user_email:
        return None  # If email could not be fetched, return None

    subject = f"Order Rejected - Order #{order_id}"
    message = f"Dear Customer,\n\nWe regret to inform you that your order #{order_id} has been rejected by our admin. " \
        f"Please feel free to contact us for further information.\n\n" \
        f"Contact Us for Support: support@yourstore.com"

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])


def send_admin_notification_email(request, order_id, user_id, address, total_price):
    # Retrieve admin's email from settings or environment variables
    # Make sure you define ADMIN_EMAIL in settings.py
    admin_email = settings.ADMIN_EMAIL

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

    # Update the order status to "canceled"
    order.status = "canceled"
    order.save()

    # Send cancellation emails to both the user and admin
    send_cancellation_email(request.session.get("uid"), order.id)

    messages.success(request, "Your order has been successfully cancelled.")
    return redirect("orders")


def send_cancellation_email(user_id, order_id):
    # Your function to fetch the user's email
    user_email = get_user_email(user_id)
    # Ensure you have ADMIN_EMAIL in settings
    admin_email = getattr(settings, "ADMIN_EMAIL", None)

    if not user_email:
        return None  # If user email is not available, do nothing

    # Email to the customer
    subject_user = f"Order Cancellation - Order #{order_id}"
    message_user = (
        f"Dear Customer,\n\n"
        f"Your order #{order_id} has been cancelled as per your request. "
        f"If you have any questions, please contact our support team at support@yourstore.com.\n\n"
        f"Best Regards,\nYour Store Team"
    )
    send_mail(subject_user, message_user,
              settings.DEFAULT_FROM_EMAIL, [user_email])

    # Email to the admin (if available)
    if admin_email:
        subject_admin = f"Order Cancellation Notification - Order #{order_id}"
        message_admin = (
            f"Dear Admin,\n\n"
            f"Order #{order_id} has been cancelled by the customer. "
            f"Please review the order details and process any further actions if needed.\n\n"
            f"Regards,\nYour Store System"
        )
        send_mail(subject_admin, message_admin,
                  settings.DEFAULT_FROM_EMAIL, [admin_email])
        
def help_support(request):
    return render(request, 'store/help_support.html')

@require_POST
def update_stock(request):
    try:
        product_id = int(request.POST.get('product_id'))
        new_stock = int(request.POST.get('new_stock'))
        
        product = Product.objects.get(id=product_id)
        # Capture the current stock before updating
        current_stock = product.stock
        
        product.stock = new_stock
        product.save()
        
        return JsonResponse({
            'success': True,
            'product_id': product_id,
            'current_stock': current_stock,  # Stock value before update
            'new_stock': product.stock       # The saved, updated stock value
        })
        
    except (Product.DoesNotExist, ValueError, TypeError) as e:
        print(f"Error updating stock: {str(e)}")
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
            SUPERADMIN_EMAIL = getattr(settings, "SUPERADMIN_EMAIL", "farazashraf413@gmail.com")
            subject = "New Admin Signup Pending Approval"
            message = (
                f"A new admin signup has been submitted.\n\n"
                f"Company Name: {company_name}\n"
                f"Email: {email}\n"
                f"Phone: {phone}\n\n"
                "Please review the signup in the Django admin panel and approve if valid."
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [SUPERADMIN_EMAIL])
            
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
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [seller_email])
        
        messages.success(request, "Seller approved and notified via email.")
        
        request.session["approval_message"] = "Approved by the ADMIN"
        return redirect("pending_seller_signups")  # Redirect to a page listing pending signups.
    else:
        # Optionally, render a confirmation page.
        return render(request, "store/admin/admin_dashboard.html", {"seller": seller})