from django.shortcuts import render, redirect
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
from django.contrib.auth.decorators import login_required
import datetime
from django.contrib import messages
from functools import wraps
import logging
from django.urls import reverse
from .services.supabase_client import supabase
from django.utils.http import urlsafe_base64_encode
# Make sure to create a ProductForm for your form handling
from .services.supabase_client import (
    # User-related  
    create_user, fetch_user_by_uid, get_user_email,
    
    # Product-related  
    upload_image, add_product as supabase_add_product,  
    fetch_all_products, delete_product, fetch_product_details,  
    update_product, get_products_by_ids,  
    
    # Order-related  
    create_order, create_order_items,  
    delete_purchased_products, delete_order, get_order_by_id, update_order_status, get_order_items, get_all_orders,
    
    # Promo codes  
    get_promo_code_details, get_promo_discount  
)
from supabase import create_client
from django.core.mail import send_mail
from django.conf import settings
from .services.supabase_client import CartService
import traceback


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
            supabase_cart = supabase.table('carts').select(
                '*').eq('user_id', uid).execute().data
            supabase_cart = {item['product_id']
                : item for item in supabase_cart}

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


def home(request):
    """Home Page - Allow all users to browse, require login only on interaction"""
    uid = request.session.get("uid")
    logger.info(f"User ID: {uid}")

    # Fetch user details only if logged in
    user_name = fetch_user_by_uid(uid) if uid else None

    # Fetch products from Supabase
    products = fetch_all_products()

    return render(request, "store/home.html", {"products": products, "user_name": user_name})


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

            # 🔹 Verify Firebase UID before inserting into Supabase
            try:
                user_record = auth.get_user(uid)
                is_verified = user_record.email_verified  # ✅ Get verification status
                # if not user_record.email_verified:
                #     return JsonResponse({"success": False, "error": "Email not verified. Please verify your email first."}, status=400)
            except firebase_admin.auth.AuthError:
                return JsonResponse({"success": False, "error": "Invalid Firebase user."}, status=400)

            # 🔹 Insert into Supabase
            supabase_response = create_user(
                uid, name, phone, email, is_verified)
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
            product_id = str(data.get('product_id'))
            uid = request.session.get("uid")

            # Extract only the image path before storing
            image_path = data.get("image_url", "")

            # Session cart handling for anonymous users
            # if not uid:
            #     cart = request.session.get('cart', {})
            #     cart_item = cart.get(product_id, {
            #         'name': data.get('name'),
            #         'category': data.get('category'),
            #         'price': float(data.get('price')),
            #         'image_url': image_path,
            #         'quantity': 0
            #     })
            #     cart_item['quantity'] += int(data.get('quantity', 1))
            #     cart[product_id] = cart_item
            #     request.session['cart'] = cart
            #     request.session.modified = True
            #     return JsonResponse({'success': True})

            if not uid:
                return JsonResponse({'success': False, 'login_required': True})

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

@admin_required
@csrf_exempt
def add_product_view(request):
    if request.method == 'GET':
        return render(request, 'store/add_product.html')

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
            # Call the updated add_product function with additional images
            product = supabase_add_product(
                name, category, price, originalPrice, description,
                image, additional_images, admin_id
            )
            print(f"🔹 Supabase Insert Response: {product}")
            if product:
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
        originalPrice = request.POST.get("originalprice")
        description = request.POST.get("description")
        image_file = request.FILES.get("image")

        # Retrieve additional images by filtering keys that start with "additional_image_"
        # Sorting by the numeric suffix ensures the order matches the HTML (e.g. additional_image_1, additional_image_2, etc.)
        additional_images = [
            file for key, file in sorted(
                request.FILES.items(), key=lambda kv: int(kv[0].split('_')[-1])
            ) if key.startswith("additional_image_")
        ]

        logger.info("🔥 Received POST request for product update.")
        logger.debug("📌 Form Data: %s", request.POST)
        logger.debug("📂 Files received: %s", request.FILES)

        logger.info("🛠 Updating Product ID: %s - %s, %s, ₹%s",
                    product_id, name, category, price)

        update_response = update_product(
            product_id,
            name=name,
            category=category,
            price=price,
            original_price=originalPrice,
            description=description,
            image_file=image_file,
            additional_images=additional_images
        )

        logger.debug("🔄 Update Response: %s", update_response)

        if "error" in update_response:
            messages.error(request, update_response["error"])
            return JsonResponse({"error": update_response["error"]}, status=400)
        else:
            messages.success(request, "Product updated successfully!")
            return JsonResponse({"success": "Product updated successfully!"}, status=200)

    return render(request, "store/admin_update_product.html", {"product": product})


@admin_required
def admin_dashboard(request):
    try:
        products_list = fetch_all_products()
        return render(request, 'store/admin_dashboard.html', {'products': products_list})
    except Exception as e:
        messages.error(request, f'Error fetching products: {str(e)}')
        return render(request, 'store/admin_dashboard.html', {'products': []})


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
    user_id = request.session.get(
        "uid")  # Firebase authentication uses session

    # Fetch cart items from Supabase
    cart_items = CartService.get_cart_summary(user_id)

    print("Cart items fetched from Supabase:", cart_items)  # Debugging

    if not cart_items:
        messages.warning(request, 'Your cart is empty')
        return redirect('/')  # Redirect to home page

    # Fetch product details for the items in the cart
    product_ids = [item['product_id'] for item in cart_items]
    products = get_products_by_ids(product_ids)  # Implement this function

    # Build validated cart with quantity
    validated_cart = {
        str(item['product_id']): {
            'name': product['name'],
            'price': product['price'],
            'image_url': product['image_url'],  # Public image URL
            'quantity': item['quantity'],  # Fetch quantity from cart
            # Multiply price by quantity
            'total_price': product['price'] * item['quantity'],
        }
        for item, product in zip(cart_items, products)
    }

    # Store validated cart in session
    request.session['cart'] = validated_cart

    print("Validated Cart Stored in Session:", validated_cart)  # Debugging
    
    # Calculate subtotal
    subtotal = sum(item['total_price'] for item in validated_cart.values())
    
    # Fixed shipping fee
    shipping = 99  

    # Get discount from frontend (ensure it's passed correctly)
    discount = float(request.GET.get('discount', 0))

    # Final total
    total = subtotal + shipping - discount



    return render(request, 'store/checkout.html', {
        'cart': validated_cart,
        'subtotal': subtotal,
        'shipping': shipping,
        'discount': discount,  # Pass the percentage
        'final_total': total
    })

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

            if not payment_method:
                return JsonResponse({"error": "Payment method is required"}, status=400)

            if not all([name, mobile, pincode, house_no, street, city, state, country]):
                return JsonResponse({"error": "All address fields are required"}, status=400)

            cart = request.session.get("cart", {})
            if not cart:
                return JsonResponse({"error": "Cart is empty"}, status=400)

            total_price = sum(
                float(item["price"]) * int(item["quantity"]) for item in cart.values()
            )

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
            order_id, error = create_order(user_id, total_price, payment_method, address_data)
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
            
            send_admin_notification_email(request, order_id, user_id, address_data, total_price)

            # Store last order and clear cart
            request.session["last_order"] = {
                "cart": cart,
                "total_price": total_price
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
    # Retrieve admin's email
    admin_email = "faraz@gmail.com"
    
    approval_url = request.build_absolute_uri(
        reverse('admin_approve_order', kwargs={'order_id': order_id, 'action': 'approve'})
    )
    rejection_url = request.build_absolute_uri(
        reverse('admin_approve_order', kwargs={'order_id': order_id, 'action': 'reject'})
    )


    # Generate the admin notification email content
    subject = f"New Order Pending Approval - Order #{order_id}"
    message = f"An order has been placed and is awaiting approval.\n\n" \
              f"Order ID: {order_id}\n" \
              f"Total Price: ₹{total_price}\n\n" \
              f"Shipping Address:\n{address.get('house_no')} {address.get('street')}\n" \
              f"{address.get('city')}, {address.get('state')}, {address.get('country')}, {address.get('pincode')}\n\n" \
              f"Click here to approve the order: {approval_url}\n" \
              f"Or click here to reject the order: {rejection_url}\n\n" \
              f"Please approve or reject the order in the admin panel."

    # Send the email to the admin's email address
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email])
    
def admin_orders(request):
    orders = get_all_orders()  # Fetch all orders
    return render(request, 'store/admin_orders.html', {'orders': orders})


@admin_required
def admin_approve_order(request, order_id, action):
    try:
        # Fetch the order from Supabase using the helper function
        order_list = get_order_by_id(order_id)
        order = order_list[0] if isinstance(order_list, list) and order_list else None

        if not order:
            return JsonResponse({"error": "Order not found"}, status=404)

        # Fetch order items to know which products were purchased
        order_items = get_order_items(order_id)
        if not order_items:
            return JsonResponse({"error": "No items found for this order"}, status=404)

        if action == "approve":
            # Update order status to confirmed
            if update_order_status(order_id, "confirmed"):
                # Delete purchased products from the store
                error = delete_purchased_products(order_items)
                if error:
                    return JsonResponse({"error": "Failed to remove purchased products."}, status=500)

                # Send confirmation email to user
                send_confirmation_email(order["user_id"], order_id, order["address"], order["total_price"])

                return JsonResponse({"success": "Order confirmed, products removed, and email sent to user."})
            else:
                return JsonResponse({"error": "Failed to update order status"}, status=500)

        elif action == "reject":
            # Update order status to rejected
            if update_order_status(order_id, "rejected"):
                # Send rejection email to the user
                send_rejection_email(order["user_id"], order_id)

                return JsonResponse({"success": "Order rejected."})
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
        # If no last order, redirect to home or orders page
        messages.error(request, "No recent order found.")
        return redirect("home")
    
    try:
        # Fetch the user's most recent order from the database
        user_id = request.session.get("uid")
        order = supabase.table("orders").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        
        if order.data:
            recent_order = order.data[0]
            
            # Fetch order items for this specific order
            order_items = supabase.table("order_items").select("*").eq("order_id", recent_order['id']).execute()
            
            context = {
                "order": recent_order,
                "order_items": order_items.data,
                "cart": last_order.get("cart", {}),
                "total_price": last_order.get("total_price", 0)
            }
            
            # Clear the last order from session
            del request.session["last_order"]
            request.session.modified = True
            
            return render(request, "store/order_success.html", context)
        else:
            messages.error(request, "Unable to retrieve order details.")
            return redirect("home")
    
    except Exception as e:
        print(f"Error fetching order details: {e}")
        messages.error(request, "An error occurred while retrieving order details.")
        return redirect("home")