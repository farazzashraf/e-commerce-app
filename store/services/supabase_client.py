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


def create_user(uid, name, phone, email):
    try:
        response = supabase.table("users").insert({
            "id": uid,  # Ensure Supabase `id` column matches Firebase UID type
            "name": name,
            "phone": phone,
            "email": email
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
        response = supabase.table("users").select("name").eq("id", uid).single().execute()
        
        # Debug log to see the full response
        print(f"User response: {response}")
        
        if hasattr(response, 'data') and response.data and "name" in response.data:
            user_name = response.data["name"]
            # Capitalize first letter only
            user_name = user_name[0].upper() + user_name[1:] if user_name else ""
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
    supabase_key = f"uploads/{timestamp}_{sanitized_filename}"  # Unique file path

    # Use a temporary file for upload
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        for chunk in image_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name

    try:
        # Upload file to Supabase storage
        response = supabase.storage.from_("product-image").upload(supabase_key, temp_file_path)

        # Remove temporary file after upload
        os.remove(temp_file_path)

        # ✅ Check for errors in response correctly
        if hasattr(response, "error") and response.error:
            raise Exception(f"Failed to upload image: {response.error}")

        return supabase_key  # Store only the path in the database

    except Exception as e:
        print(f"❌ Upload Error: {str(e)}")
        return None

def add_product(name, category, price, description, image_url, admin_id):
    """Add a new product to the Supabase database."""

    print(f"🔹 Received Admin ID: {admin_id}")  # Debugging

    try:

        print(f"✅ Converted Admin ID to UUID: {admin_id}")  # Debugging
        print(f"🔹 Attempting to insert data into Supabase:")
        print(f"   Name: {name}")
        print(f"   Category: {category}")
        print(f"   Price: {price}")
        print(f"   Description: {description}")
        print(f"   Image URL: {image_url}")
        print(f"   Admin ID: {admin_id}")

        data = {
            "name": name,
            'category': category,
            "price": price,
            "description": description,
            "image_url": image_url,
            "admin_id": admin_id
        }

        print(f"🔹 Inserting Data: {data}")  # Debugging

        response = supabase.table('products').insert(data).execute()
        print(f"✅ Insert response: {response}")

        # Check if the insert failed
        if "error" in response:
            print(f"❌ Supabase Insert Error: {response['error']}")
            return None

        return response.data if hasattr(response, 'data') else None

    except Exception as e:
        print(f"❌ Error inserting product: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None
    
def fetch_product_details(product_id):
    """Fetch a product's details from Supabase."""
    try:
        response = supabase.table("products").select("*").eq("id", product_id).single().execute()

        # Ensure response.data exists and is a dictionary
        if not response.data:
            return {"error": f"Product with ID {product_id} not found."}

        product = response.data  # Directly extract data
        image_path = product.get("image_url")  # Ensure key exists

        # Generate the public URL for the image
        if image_path:
            product["image_url"] = supabase.storage.from_("product-image").get_public_url(image_path)

        return product  # Return product details as a dictionary

    except Exception as e:
        return {"error": f"Error fetching product details: {str(e)}"}


    except Exception as e:
        return {"error": f"Error fetching product details: {str(e)}"}


def update_product(product_id, name=None, category=None, price=None, description=None, image_file=None):
    """Update an existing product in the Supabase database."""
    try:
        update_data = {}

        if name:
            update_data["name"] = name
        if category:
            update_data["category"] = category
        if price:
            update_data["price"] = price
        if description:
            update_data["description"] = description

        # Handle image update
        if image_file:
            new_image_url = upload_image(image_file)  # Upload new image
            update_data["image_url"] = new_image_url

            # Fetch current product details to delete the old image
            response = supabase.table("products").select("image_url").eq("id", product_id).single().execute()

            if response.data and "image_url" in response.data:
                old_image_url = response.data["image_url"]
                if old_image_url:
                    print(f"Old image URL: {old_image_url}")  # Log the old image URL for debugging
                    supabase.storage.from_("product-image").remove([old_image_url])

        if not update_data:
            return {"error": "No fields provided for update"}

        # Update the product
        response = supabase.table("products").update(update_data).eq("id", product_id).execute()

        # Log the full response for debugging
        print("Supabase Update Response:", response)

        # Ensure response is returned as a dictionary
        if hasattr(response, "error") and response.error:
            print(f"Supabase Update Error: {response.error}")
            return {"error": str(response.error)}

        return {"success": "Product updated successfully"}

    except Exception as e:
        print(f"Exception: {e}")  # Log the exception
        return {"error": str(e)}


def fetch_all_products():
    """Fetch all products from Supabase and ensure correct column mapping."""
    try:
        response = (
            supabase
            .table("products")
            # Explicitly fetch correct fields
            .select("id, name, category, price, description, image_url")
            .execute()
        )

        products = response.data if hasattr(response, "data") else []

        # Debugging: Print the fetched data to check if columns are correct
        print(f"✅ Fetched Products: {products}")

        # Generate public URLs for product images
        for product in products:
            image_path = product["image_url"]
            product["image_url"] = supabase.storage.from_(
                "product-image").get_public_url(image_path)

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
        response = supabase.table("promo_codes").select("discount", "valid").eq("code", promo_code).execute()
        
        if response.data and response.data[0]["valid"]:
            return {"success": True, "discount": response.data[0]["discount"]}
        return {"success": False, "error": "Invalid or expired promo code"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
