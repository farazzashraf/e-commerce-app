import os
import tempfile
from supabase import create_client
from dotenv import load_dotenv
from django.core.files.uploadedfile import InMemoryUploadedFile
import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
import json
from datetime import datetime

import logging
import re
from django.http import JsonResponse
import traceback

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


def create_user(uid, name, phone, email, is_verified):
    try:
        response = supabase.table("users").insert({
            "id": uid,  # Ensure Supabase `id` column matches Firebase UID type
            "name": name,
            "phone": phone,
            "email": email,
            "is_verified": is_verified
        }).execute()

        if response.data:  # Correct way to access response data
            return JsonResponse({"message": "User inserted into Supabase"}, status=201)
        else:
            return JsonResponse({"error": "Supabase insert failed"}, status=500)

    except Exception as e:
        print(f"Error inserting user into Supabase: {str(e)}")
        return False


def fetch_user_by_uid(uid):
    """Fetch user name from Supabase by user ID"""
    try:
        response = supabase.table("users").select(
            "name").eq("id", uid).single().execute()

        # Debug log to see the full response
        print(f"User response: {response}")

        if hasattr(response, 'data') and response.data and "name" in response.data:
            user_name = response.data["name"]
            # Capitalize first letter only
            user_name = user_name[0].upper(
            ) + user_name[1:] if user_name else ""
            print(f"✅ Fetched user name: {user_name}")
            return user_name
        else:
            print("❌ No user data found or name not available")
            return ""

    except Exception as e:
        print(f"❌ Error fetching user: {str(e)}")
        import traceback
        traceback.print_exc()
        return ""


def search_products(query: str):
    """
    Function to search products by name or description.
    It performs a case-insensitive search using the `ilike` operator.
    """
    # Query Supabase for products that match the search term in name or description
    response = supabase.table('products').select('*') \
        .ilike('name', f'%{query}%') \
        .or_('description.ilike', f'%{query}%') \
        .execute()

    if response.get('status_code') == 200:
        return response['data']  # Return product data from the response
    return []


def sanitize_filename(filename):
    """Removes invalid characters and replaces spaces with underscores."""
    filename = filename.replace(" ", "_")  # Replace spaces
    filename = re.sub(r'[^\w\-.]', '', filename)  # Remove special characters
    return filename


def upload_image(image_file):
    """Uploads an image to Supabase storage and returns the public URL."""
    if not image_file:
        return None  # No file provided

    # Generate a sanitized filename with a timestamp to prevent duplicates
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    sanitized_filename = sanitize_filename(image_file.name)
    # Unique file path
    supabase_key = f"uploads/{timestamp}_{sanitized_filename}"

    # Use a temporary file for upload
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        for chunk in image_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name

    try:
        # Upload file to Supabase storage
        response = supabase.storage.from_(
            "product-image").upload(supabase_key, temp_file_path)

        # Remove temporary file after upload
        os.remove(temp_file_path)

        # ✅ Check for errors in response correctly
        if hasattr(response, "error") and response.error:
            raise Exception(f"Failed to upload image: {response.error}")

        return supabase_key  # Store only the path in the database

    except Exception as e:
        print(f"❌ Upload Error: {str(e)}")
        return None

def add_product(name, category, price, originalPrice, description, image_file, additional_image_files, admin_id):
    """Add a new product to Supabase with additional images."""
    # Upload main image
    main_image_url = upload_image(image_file)

    # Upload additional images (up to 3)
    additional_urls = []
    if additional_image_files:
        for img in additional_image_files:
            url = upload_image(img)
            if url:
                additional_urls.append(url)

    data = {
        "name": name,
        "category": category,
        "price": price,
        "original_price": originalPrice,
        "description": description,
        "image_url": main_image_url,
        "admin_id": admin_id
    }
    if len(additional_urls) > 0:
        data["image_url2"] = additional_urls[0]
    if len(additional_urls) > 1:
        data["image_url3"] = additional_urls[1]
    if len(additional_urls) > 2:
        data["image_url4"] = additional_urls[2]

    try:
        response = supabase.table('products').insert(data).execute()
        print(f"✅ Insert response: {response}")
        if "error" in response:
            print(f"❌ Supabase Insert Error: {response['error']}")
            return None
        return response.data if hasattr(response, 'data') else None
    except Exception as e:
        print(f"❌ Error inserting product: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def fetch_product_details(product_id):
    """Fetch product details, including additional images with public URLs."""
    try:
        response = supabase.table("products").select(
            "*").eq("id", product_id).single().execute()

        if not response.data:
            return {"error": f"Product with ID {product_id} not found."}

        product = response.data

        # Get the public URL for the main image
        if product.get("image_url"):
            product["image_url"] = supabase.storage.from_(
                "product-image").get_public_url(product["image_url"])

        # Collect additional images with public URLs
        additional_images = []
        for key in ["image_url2", "image_url3", "image_url4"]:
            if product.get(key):
                public_url = supabase.storage.from_(
                    "product-image").get_public_url(product[key])
                additional_images.append(public_url)

        product["additional_images"] = additional_images

        return product
    except Exception as e:
        return {"error": f"Error fetching product details: {str(e)}"}

def update_product(product_id, name=None, category=None, price=None, original_price=None, 
                   description=None, image_file=None, additional_images=None):
    """Update an existing product in the Supabase database with optional additional images."""
    try:
        update_data = {}

        if name:
            update_data["name"] = name
        if category:
            update_data["category"] = category
        if price:
            update_data["price"] = float(price)  # Ensure numeric type
        if original_price:
            update_data["original_price"] = float(original_price)  # Ensure numeric type
        if description:
            update_data["description"] = description

        # Handle main image update
        if image_file:
            new_image_url = upload_image(image_file)  # Upload new image
            update_data["image_url"] = new_image_url

            # Fetch current product details to delete the old main image
            response = supabase.table("products").select("image_url").eq("id", product_id).single().execute()
            if response.data and "image_url" in response.data:
                old_image_url = response.data["image_url"]
                if old_image_url:
                    logger.debug("🗑️ Deleting old image: %s", old_image_url)
                    supabase.storage.from_("product-image").remove([old_image_url])

        # Handle additional images update
        if additional_images:
            # Upload each additional image
            new_image_urls = [upload_image(img) for img in additional_images if img]

            # Remove duplicate URLs while preserving order (if needed)
            unique_new_image_urls = []
            for url in new_image_urls:
                if url not in unique_new_image_urls:
                    unique_new_image_urls.append(url)

            # Fetch current additional images to know what already exists
            response = supabase.table("products").select("image_url2, image_url3, image_url4") \
                        .eq("id", product_id).single().execute()
            old_images = response.data if response.data else {}

            # Update additional image columns:
            if len(unique_new_image_urls) > 0:
                update_data["image_url2"] = unique_new_image_urls[0]
            if len(unique_new_image_urls) > 1:
                update_data["image_url3"] = unique_new_image_urls[1]
            if len(unique_new_image_urls) > 2:
                update_data["image_url4"] = unique_new_image_urls[2]

            # Clear any columns that are not updated
            # Our additional images map to image_url2, image_url3, and image_url4
            for i in range(len(unique_new_image_urls), 3):
                update_data[f"image_url{i+2}"] = None

            # Identify replaced images for cleanup (compare new URLs with the old ones)
            old_urls = []
            for i in range(2, 5):  # iterate over image_url2, image_url3, image_url4
                new_url = update_data.get(f"image_url{i}")
                old_url = old_images.get(f"image_url{i}")
                if new_url and old_url and new_url != old_url:
                    old_urls.append(old_url)

            if old_urls:
                logger.debug("🗑️ Deleting old additional images: %s", old_urls)
                supabase.storage.from_("product-image").remove(old_urls)

        if not update_data:
            return {"error": "No fields provided for update"}

        logger.debug("🛠 Update data to send: %s", update_data)
        
        # Update the product in Supabase
        response = supabase.table("products").update(update_data).eq("id", product_id).execute()
        logger.debug("🔄 Supabase Update Response: %s", response)

        if response.data:
            logger.info("✅ Updated product successfully: %s", response.data)
            return {"success": "Product updated successfully"}
        else:
            logger.error("❌ Error updating product: %s", response.error)
            return {"error": response.error}
    
    except Exception as e:
        logger.exception("🚨 Exception in update_product: %s", str(e))
        return {"error": str(e)}

def fetch_all_products():
    """Fetch all products from Supabase with all image URLs"""
    try:
        response = (
            supabase
            .table("products")
            .select("""
                id, 
                name, 
                category, 
                price, 
                original_price, 
                description, 
                created_at,
                image_url,
                image_url2,
                image_url3,
                image_url4
            """)
            .execute()
        )

        products = response.data if hasattr(response, "data") else []

        # Convert all image URLs to public URLs
        for product in products:
            for i in range(1, 5):
                key = f"image_url{i}" if i > 1 else "image_url"
                if product.get(key):
                    product[key] = supabase.storage.from_(
                        "product-image").get_public_url(product[key])
        
        # Convert timestamps to formatted string
        for product in products:
            if product.get("created_at"):
                product["created_at"] = datetime.strptime(product["created_at"], "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S")

        print(f"✅ Fetched Products with images: {products}")
        return products

    except Exception as e:
        print(f"❌ Error fetching products: {str(e)}")
        return []


def delete_product(request, product_id):
    """Deletes a product from Supabase and redirects to the dashboard."""
    try:
        # Fetch the product details to get the image path
        response = supabase.table("products").select(
            "image_url").eq("id", product_id).single().execute()

        if response.data and "image_url" in response.data:
            image_path = response.data["image_url"]

            # Delete the image from Supabase Storage
            storage_response = supabase.storage.from_(
                "product-image").remove([image_path])

            # ✅ Fix: Only show an error if the response indicates failure
            if isinstance(storage_response, list) and storage_response:
                first_item = storage_response[0]  # Get first response item
                if "error" in first_item:  # Check if it contains an error
                    messages.error(
                        request, f"Error deleting image: {first_item['error']}")
                else:
                    # ✅ Debugging log
                    print(f"🟢 Image deleted successfully: {image_path}")

        # ✅ Delete the product from all users' carts before deleting the product itself
        cart_delete_response = supabase.table("carts").delete().eq(
            "product_id", product_id).execute()

        if hasattr(cart_delete_response, "error") and cart_delete_response.error:
            messages.error(
                request, f"Failed to delete product from carts: {cart_delete_response.error}")
        else:
            print(f"🟢 Product removed from carts successfully: {product_id}")

        # Delete the product from Supabase Database
        delete_response = supabase.table(
            "products").delete().eq("id", product_id).execute()

        if hasattr(delete_response, "error") and delete_response.error:
            messages.error(
                request, f"Failed to delete product: {delete_response.error}")
        else:
            messages.success(request, "Product deleted successfully.")

    except Exception as e:
        messages.error(request, f"Error deleting product: {str(e)}")

    return redirect("admin_dashboard")

# supabaseclient.py


class CartService:
    @staticmethod
    def add_to_cart(uid, product_id, product_data):
        """Add/update item in cart"""
        try:
            # For authenticated users
            if uid:
                existing_cart_item = supabase.table('carts').select('quantity')\
                    .eq('user_id', uid)\
                    .eq('product_id', product_id)\
                    .execute().data
                if existing_cart_item:
                    new_quantity = existing_cart_item[0]['quantity'] + \
                        product_data['quantity']
                    return supabase.table('carts').update({'quantity': new_quantity})\
                        .eq('user_id', uid)\
                        .eq('product_id', product_id)\
                        .execute()
                else:
                    return supabase.table('carts').upsert({
                        'user_id': uid,
                        'product_id': product_id,
                        **product_data
                    }).execute().data
            # Anonymous users handled via session
            return None
        except Exception as e:
            raise ValueError(f"Supabase add error: {str(e)}")

    @staticmethod
    def remove_from_cart(uid, product_id):
        """Remove item from cart"""
        try:
            if uid:
                return supabase.table('carts').delete()\
                    .eq('user_id', uid)\
                    .eq('product_id', product_id)\
                    .execute()
            return None
        except Exception as e:
            raise ValueError(f"Supabase remove error: {str(e)}")

    @staticmethod
    def update_cart_quantity(uid, product_id, quantity):
        """Update item quantity in cart"""
        try:
            if uid:
                return supabase.table('carts').update({'quantity': quantity})\
                    .eq('user_id', uid)\
                    .eq('product_id', product_id)\
                    .execute()
            return None
        except Exception as e:
            raise ValueError(f"Supabase update error: {str(e)}")

    @staticmethod
    def get_cart_items(uid):
        """Get all cart items for user"""
        try:
            if uid:
                return supabase.table('carts').select('*').eq('user_id', uid).execute().data
            return []
        except Exception as e:
            raise ValueError(f"Supabase fetch error: {str(e)}")
        
    @staticmethod
    def get_cart_summary(uid):
        """Fetch only product_id and quantity for order validation"""
        try:
            if uid:
                result = supabase.table('carts')\
                    .select('product_id, quantity')\
                    .eq('user_id', uid)\
                    .execute()
                print(f"✅ Cart summary fetched: {result.data}")
                return result.data
            return []
        except Exception as e:
            print(f"❌ Supabase summary fetch error: {str(e)}")
            return []

    @staticmethod
    def get_cart_count(uid):
        """Get total item count in cart"""
        try:
            if uid:
                result = supabase.table('carts').select(
                    'quantity').eq('user_id', uid).execute()
                return sum(item['quantity'] for item in result.data)
            return 0
        except Exception as e:
            raise ValueError(f"Supabase count error: {str(e)}")


def get_promo_code_details(promo_code: str):
    """Fetch promo code details from Supabase."""
    try:
        response = supabase.table("promo_codes").select(
            "discount", "valid").eq("code", promo_code).execute()

        if response.data and response.data[0]["valid"]:
            return {"success": True, "discount": response.data[0]["discount"]}
        return {"success": False, "error": "Invalid or expired promo code"}

    except Exception as e:
        return {"success": False, "error": str(e)}

def get_promo_discount(promo_code):
    """Fetch promo discount from Supabase."""
    response = supabase.table('promo_codes').select('*').eq('code', promo_code).execute()
    return response.data[0]['discount'] if response.data else 0
    
def get_products_by_ids(product_ids):
    """Fetch products from Supabase by their IDs and convert image URLs to public URLs."""
    response = supabase.table('products').select('*').in_('id', product_ids).execute()
    products = response.data if response.data else []

    # Convert all image URLs to public URLs
    for product in products:
        if product.get("image_url"):  # Ensure key exists
            product["image_url"] = supabase.storage.from_("product-image").get_public_url(product["image_url"])

    return products

def create_order(user_id, total_price, payment_method, address_data):
    order_data = {
        "user_id": user_id,
        "total_price": total_price,
        "payment_method": payment_method,
        "address": json.dumps(address_data),  # Ensure address_data is serialized properly
        "status": "pending",
    }
    
    print("🔹 Order Data Being Sent to Supabase:", order_data)  # Debugging

    response = supabase.table("orders").insert(order_data).execute()
    
    if response.data:
        return response.data[0]["id"], None  # Return the order_id
    
    if response.data:
        return response.data[0]["id"], None  # ✅ Correct

    # ✅ Log failure if order was not created
    print("❌ Order creation failed:", response)
    return None, "Order creation failed"



def create_order_items(order_id, cart):
    try:
        order_items = []
        for product_id, item in cart.items():
            # Ensure product_id is converted to an integer
            product_id = int(product_id)
            
            order_item = {
                "order_id": order_id,  # int4
                "product_id": product_id,  # int4
                "name": item["name"],  # text
                "price": float(item["price"]),  # numeric
                "quantity": int(item["quantity"]),  # int4
                "total_price": float(item["total_price"]),  # numeric
            }
            order_items.append(order_item)

        print("🔹 Order Items Data to Insert:", order_items)  # Debugging

        # Insert order items into Supabase
        response = supabase.table("order_items").insert(order_items).execute()

        # Check the response carefully
        print("Full Supabase Response:", response)
        
        # Verify data was inserted
        if hasattr(response, 'data') and response.data:
            print("✅ Order Items Created successfully.")
            return None
        else:
            print(f"❌ Failed to create order items. Raw Response: {response}")
            return f"Failed to create order items: {response}"

    except Exception as e:
        print(f"❌ Exception in create_order_items: {e}")
        import traceback
        traceback.print_exc()
        return str(e)
    
def delete_order(order_id):
    try:
        # Call Supabase to delete the order
        response = supabase.table("orders").delete().eq("id", order_id).execute()
        
        # Check deletion success using response.data
        if response.data:
            print(f"✅ Order ID {order_id} deleted successfully.")
            return None
        else:
            print(f"❌ Failed to delete order ID {order_id}. Response: {response}")
            return "Failed to delete order"

    except Exception as e:
        print(f"❌ Exception in delete_order: {e}")  # Debugging
        return str(e)


def delete_purchased_products(cart):
    """Mark purchased products as inactive in Supabase database and clean up cart."""
    product_ids = [int(product_id) for product_id in cart.keys()]

    print("🛑 Marking products with IDs as inactive:", product_ids)  # Debugging log

    try:
        # Fetch product details to get image URLs before updating
        response = supabase.table("products").select("id, image_url").in_("id", product_ids).execute()

        # if response.data:
        #     image_urls = [product["image_url"] for product in response.data if "image_url" in product]

        #     if image_urls:
        #         # Delete images from Supabase Storage
        #         storage_response = supabase.storage.from_("product-image").remove(image_urls)

        #         if isinstance(storage_response, list) and storage_response:
        #             first_item = storage_response[0]
        #             if "error" in first_item:
        #                 print("❌ Error deleting images:", first_item["error"])
        #             else:
        #                 print("🟢 Images deleted successfully:", image_urls)
        #         else:
        #             print("🟢 Images deleted successfully:", image_urls)

        # ✅ Update products to mark as inactive in Supabase database
        update_products_response = supabase.table("products").update({"is_active": False}).in_("id", product_ids).execute()

        if update_products_response.data:
            print("✅ Products marked as inactive successfully.")

            # ✅ Delete corresponding entries from the `cart` table
            delete_cart_response = supabase.table("carts").delete().in_("product_id", product_ids).execute()

            if delete_cart_response.data:
                print("✅ Cart entries deleted successfully.")
                return None  # No error
            else:
                print("❌ Failed to delete cart entries:", delete_cart_response)
                return "Failed to delete cart entries"

        print("❌ Failed to mark products as inactive:", update_products_response)
        return "Failed to mark products as inactive"

    except Exception as e:
        print("❌ Exception while processing products:", str(e))
        return "Error processing products"

def get_user_email(user_id):
    try:
        response = supabase.table("users").select("email").eq("id", user_id).single().execute()

        if response.data:  # Check if data exists
            return response.data[0]["email"]  # Extract email correctly
        
        return None  # No user found
    
    except Exception as e:
        print(f"Error fetching user email: {str(e)}")
        return None  # Return None on error


def get_order_by_id(order_id: int) -> dict:
    response = supabase.table('orders').select('*').eq('id', order_id).execute()

    if not response.data:
        return None  # Order not found
    return response.data[0]  # Return the first order, as we're querying by ID

def update_order_status(order_id: int, status: str) -> bool:
    """Updates the status of the order in the Supabase database."""
    response = supabase.table('orders').update({"status": status}).eq('id', order_id).execute()
    
    # Check if the update was successful
    if response.data:
        return "update succeessful"
    return False

def get_order_items(order_id):
    try:
        response = supabase.table("order_items").select("product_id").eq("order_id", order_id).execute()

        if response.data:
            return [item["product_id"] for item in response.data]  # Return list of product IDs
        
        return None  # No items found

    except Exception as e:
        print(f"Error fetching order items: {str(e)}")
        return None  # Return None on error

def get_all_orders():
    try:
        response = supabase.table("orders").select("*").execute()
        if not response.data:
            return []  # Return empty list if no orders found

        orders = []
        for order in response.data:
            order_items = get_order_items(order["id"])  # Fetch associated products
            order["items"] = order_items if order_items else []  # Attach product IDs
            orders.append(order)

        return orders

    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        return []