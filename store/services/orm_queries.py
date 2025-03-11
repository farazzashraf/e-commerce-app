from store.models import Product, User, Cart, PromoCode, Order, OrderItem, AdminStore
import logging
from django.core.files.storage import default_storage
from datetime import datetime
import re
import tempfile
from dotenv import load_dotenv
import os
from supabase import create_client
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.db.models import Q
from django.db.models import F
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
import traceback
import json

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
    """Create or get an existing user by UID"""
    try:
        user, created = User.objects.get_or_create(
            id=uid,  # Use Firebase UID as primary key
            defaults={
                "name": name,
                "phone": phone,
                "email": email,
                "is_verified": is_verified,
            }
        )

        if not created:
            logger.warning(f"User with UID {uid} already exists.")
            return None  # User already exists, no need to create again

        return user  # Successfully created user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None


def get_user_by_uid(uid):
    """Fetch user details by UID"""
    try:
        user = User.objects.get(id=uid)
        return user
    except User.DoesNotExist:
        logger.warning(f"No user found with UID: {uid}")
        return None


def get_all_products():
    """Fetch all products from database with all image URLs converted to public URLs"""
    try:
        # Fetch all products using Django ORM
        products = list(Product.objects.filter(is_active=True, is_deleted=False).values(
            'id',
            'name',
            'category',
            'price',
            'original_price',
            'description',
            'created_at',
            'image_url',
            'image_url2',
            'image_url3',
            'image_url4',
            'stock'
        ))

        # Convert image URLs to public URLs
        for product in products:
            for i in range(1, 5):
                key = f'image_url{i}' if i > 1 else 'image_url'
                if product.get(key):
                    product[key] = supabase.storage.from_(
                        'product-image').get_public_url(product[key])

        # Convert datetime objects to formatted strings
        for product in products:
            if product['created_at']:
                product['created_at'] = product['created_at'].strftime(
                    "%Y-%m-%d %H:%M:%S")

        print(f"✅ Fetched Products with images: {products}")
        return products

    except Exception as e:
        print(f"❌ Error fetching products: {str(e)}")
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

        logger.info(f"Upload response: {response}")
        if hasattr(response, "error") and response.error:
            logger.error(f"Upload error: {response.error}")
            raise Exception(f"Failed to upload image: {response.error}")

        # Remove temporary file after upload
        os.remove(temp_file_path)

        # ✅ Check for errors in response correctly
        if hasattr(response, "error") and response.error:
            raise Exception(f"Failed to upload image: {response.error}")

        return supabase_key  # Store only the path in the database

    except Exception as e:
        print(f"❌ Upload Error: {str(e)}")
        return None


def orm_add_product(name, category, price, original_price, description, image_file, additional_image_files, admin_id):
    """
    Add a new product using Django ORM.
    The admin_id is stored as a TextField.
    """
    # Upload the main image and get its URL
    main_image_url = upload_image(image_file)

    # Upload additional images (up to 3) and collect their URLs
    additional_urls = []
    if additional_image_files:
        for img in additional_image_files:
            url = upload_image(img)
            if url:
                additional_urls.append(url)

    # Create the Product instance using Django ORM, including admin_id
    product = Product.objects.create(
        name=name,
        category=category,
        price=price,
        original_price=original_price,
        description=description,
        image_url=main_image_url,
        admin_id=admin_id,
    )

    # Assign additional image URLs if available
    if len(additional_urls) > 0:
        product.image_url2 = additional_urls[0]
    if len(additional_urls) > 1:
        product.image_url3 = additional_urls[1]
    if len(additional_urls) > 2:
        product.image_url4 = additional_urls[2]

    # Save the updates if any additional images were set after creation
    product.save()

    return product


def fetch_all_products():
    """
    Fetch all products using Django ORM and convert stored image keys into public URLs.
    """
    try:
        # Fetch all products ordered by creation date (newest first)
        products_queryset = Product.objects.filter(
            is_deleted=False).order_by("-created_at")
        products = []

        # Iterate over each product and convert it into a dict
        for product in products_queryset:
            product_data = {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "original_price": product.original_price,
                "description": product.description,
                "created_at": product.created_at.strftime("%Y-%m-%d %H:%M:%S") if product.created_at else "",
                # Convert stored image keys to public URLs using Supabase's API
                "image_url": supabase.storage.from_("product-image").get_public_url(product.image_url) if product.image_url else None,
                "image_url2": supabase.storage.from_("product-image").get_public_url(product.image_url2) if product.image_url2 else None,
                "image_url3": supabase.storage.from_("product-image").get_public_url(product.image_url3) if product.image_url3 else None,
                "image_url4": supabase.storage.from_("product-image").get_public_url(product.image_url4) if product.image_url4 else None,
                "is_active": product.is_active,
                "stock": product.stock,
            }
            products.append(product_data)

        logger.info(f"✅ Fetched Products with images: {products}")
        return products

    except Exception as e:
        logger.error(f"❌ Error fetching products: {str(e)}")
        return []


def delete_product(request, product_id):
    """
    Deletes a product using Django ORM:
    - Deletes its associated image file from Supabase storage.
    - Removes the product from any carts.
    - Deletes the product record from the local database.
    """
    try:
        # Fetch the product using Django ORM; returns 404 if not found.
        product = get_object_or_404(Product, id=product_id)

        # Delete the product image from Supabase storage if it exists.
        image_path = product.image_url
        if image_path:
            storage_response = supabase.storage.from_(
                "product-image").remove([image_path])
            if isinstance(storage_response, list) and storage_response:
                # Get the first response item.
                first_item = storage_response[0]
                if "error" in first_item:
                    messages.error(
                        request, f"Error deleting image: {first_item['error']}")
                else:
                    print(f"🟢 Image deleted successfully: {image_path}")

        # Delete the product from all users' carts.
        # Assuming your Cart model has a field 'product_id' or a ForeignKey to Product.
        carts_deleted, _ = Cart.objects.filter(product_id=product_id).delete()
        if carts_deleted:
            print(f"🟢 Product removed from carts successfully: {product_id}")

        # Instead of a hard delete, mark the product as deleted.
        product.is_deleted = True
        product.save()
        messages.success(request, "Product deleted successfully.")

        # # Delete the product record from the database.
        # product.delete()
        # messages.success(request, "Product deleted successfully.")

    except Exception as e:
        messages.error(request, f"Error deleting product: {str(e)}")

    return redirect("admin_dashboard")


def fetch_product_details_orm(product_id):
    """
    Fetch product details using Django ORM,
    including additional images with public URLs.
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return {"error": f"Product with ID {product_id} not found."}

    # Get the public URL for the main image if it exists
    main_image_url = (
        supabase.storage.from_(
            "product-image").get_public_url(product.image_url)
        if product.image_url else None
    )

    # Collect additional images with public URLs
    additional_images = []
    for image_field in ["image_url2", "image_url3", "image_url4"]:
        image_value = getattr(product, image_field, None)
        if image_value:
            public_url = supabase.storage.from_(
                "product-image").get_public_url(image_value)
            additional_images.append(public_url)

    product_details = {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "original_price": product.original_price,
        "description": product.description,
        "image_url": main_image_url,
        "additional_images": additional_images,
    }
    return product_details


def orm_update_product(product_id, name=None, category=None, price=None, original_price=None,
                       description=None, image_file=None, additional_images=None):
    """
    Update an existing product using Django ORM.
    Image files are uploaded to Supabase storage via upload_image, and any replaced images are removed.
    """
    try:
        # Retrieve the product from the local database
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        logger.error("Product not found for id: %s", product_id)
        return {"error": "Product not found."}

    # List to keep track of changed fields for an efficient save
    updated_fields = []

    # Update text and numeric fields if provided
    if name is not None:
        product.name = name
        updated_fields.append("name")
    if category is not None:
        product.category = category
        updated_fields.append("category")
    if price is not None:
        product.price = float(price)
        updated_fields.append("price")
    if original_price is not None:
        product.original_price = float(original_price)
        updated_fields.append("original_price")
    if description is not None:
        product.description = description
        updated_fields.append("description")

    # Handle main image update
    if image_file:
        # Upload new image to Supabase storage
        new_image_url = upload_image(image_file)
        if new_image_url:
            # Remove old main image if exists
            if product.image_url:
                logger.debug("🗑️ Deleting old main image: %s",
                             product.image_url)
                supabase.storage.from_(
                    "product-image").remove([product.image_url])
            product.image_url = new_image_url
            updated_fields.append("image_url")

    # Handle additional images update
    if additional_images:
        # Upload each additional image
        new_image_urls = [upload_image(img)
                          for img in additional_images if img]
        # Remove duplicates while preserving order
        unique_new_image_urls = []
        for url in new_image_urls:
            if url not in unique_new_image_urls:
                unique_new_image_urls.append(url)

        # Save old additional image URLs for cleanup (if replaced)
        old_urls = []
        # Update image_url2
        if len(unique_new_image_urls) >= 1:
            if product.image_url2 and product.image_url2 != unique_new_image_urls[0]:
                old_urls.append(product.image_url2)
            product.image_url2 = unique_new_image_urls[0]
            updated_fields.append("image_url2")
        else:
            if product.image_url2:
                old_urls.append(product.image_url2)
            product.image_url2 = None
            updated_fields.append("image_url2")
        # Update image_url3
        if len(unique_new_image_urls) >= 2:
            if product.image_url3 and product.image_url3 != unique_new_image_urls[1]:
                old_urls.append(product.image_url3)
            product.image_url3 = unique_new_image_urls[1]
            updated_fields.append("image_url3")
        else:
            if product.image_url3:
                old_urls.append(product.image_url3)
            product.image_url3 = None
            updated_fields.append("image_url3")
        # Update image_url4
        if len(unique_new_image_urls) >= 3:
            if product.image_url4 and product.image_url4 != unique_new_image_urls[2]:
                old_urls.append(product.image_url4)
            product.image_url4 = unique_new_image_urls[2]
            updated_fields.append("image_url4")
        else:
            if product.image_url4:
                old_urls.append(product.image_url4)
            product.image_url4 = None
            updated_fields.append("image_url4")

        # Remove any replaced additional images from Supabase storage
        if old_urls:
            logger.debug("🗑️ Deleting old additional images: %s", old_urls)
            supabase.storage.from_("product-image").remove(old_urls)

    if not updated_fields:
        return {"error": "No fields provided for update."}

    # Save only the fields that were updated
    product.save(update_fields=updated_fields)
    logger.info("✅ Updated product successfully: %s", product)
    return {"success": "Product updated successfully."}


class CartService:
    @staticmethod
    def add_to_cart(uid, product_id, product_data):
        """Add/update item in cart using Django ORM."""
        try:
            # Get user and product instances
            user = User.objects.get(id=uid)
            product = Product.objects.get(id=int(product_id), is_active=True)
            
            # Retrieve the requested quantity; default to 1 if not provided.
            requested_qty = int(product_data.get('quantity', 1))
            
            # Check if the requested quantity exceeds available stock.
            if requested_qty > product.stock:
                raise ValueError("Requested quantity exceeds available stock.")

            existing_item = Cart.objects.filter(
                user_id=user,
                product_id=product
            ).first()

            if existing_item:
                new_total = existing_item.quantity + requested_qty
                if new_total > product.stock:
                    available = product.stock - existing_item.quantity
                    if available == 0:
                        raise ValueError("No more stock available for this product.")
                    else:
                        raise ValueError(f"You can add {available} more item{'s' if available != 1 else ''} to your cart")
                
                existing_item.quantity = new_total
                existing_item.save()
                return existing_item
            
            # Otherwise, create a new cart item.
            return Cart.objects.create(
                user_id=user,
                product_id=product,
                **{k: v for k, v in product_data.items() if k != 'product_id'}
            )

        except User.DoesNotExist:
            raise ValueError("User does not exist")
        except Product.DoesNotExist:
            raise ValueError("Product does not exist")
        except Exception as e:
            raise ValueError(str(e))


    @staticmethod
    def remove_from_cart(uid, product_id):
        """Remove item from cart using Django ORM."""
        try:
            user = User.objects.get(id=uid)
            product = Product.objects.get(id=int(product_id))
            Cart.objects.filter(user_id=user, product_id=product).delete()
            return True
        except (User.DoesNotExist, Product.DoesNotExist) as e:
            raise ValueError(f"Invalid ID: {str(e)}")
        except Exception as e:
            raise ValueError(f"Django ORM remove error: {str(e)}")

    @staticmethod
    def update_cart_quantity(uid, product_id, quantity):
        """Update item quantity in cart using Django ORM."""
        try:
            user = User.objects.get(id=uid)
            product = Product.objects.get(id=int(product_id))
            cart_item = Cart.objects.filter(user_id=user).first()

            if cart_item:
                quantity = int(quantity)
                # Check if the new quantity exceeds available product stock.
                if quantity > product.stock:
                    raise ValueError(
                        "Requested quantity exceeds available stock.")
                cart_item.quantity = quantity
                cart_item.save()
                return cart_item
            return None
        except (User.DoesNotExist, Product.DoesNotExist) as e:
            raise ValueError(f"Invalid ID: {str(e)}")
        except Exception as e:
            raise ValueError(f"Django ORM update error: {str(e)}")

    @staticmethod
    def get_cart_items(uid):
        """Get all cart items for user"""
        try:
            user = User.objects.get(id=uid)
            return list(Cart.objects.filter(user_id=user, product_id__is_active=True).values(
                'product_id__id',  # Actual product ID
                'quantity',
                'name',
                'price',
                'image_url',
                'category'
            ))
        except User.DoesNotExist:
            return []
        except Exception as e:
            raise ValueError(f"Django ORM fetch error: {str(e)}")

    @staticmethod
    def get_cart_summary(uid):
        """Fetch product_id and quantity for order validation."""
        try:
            user = User.objects.get(id=uid)
            cart_items = list(
                Cart.objects.filter(user_id=user).values(
                    'product_id__id', 'quantity')
            )
            # Rename 'product_id__id' to 'product_id' in the output dictionaries.
            for item in cart_items:
                item['product_id'] = item.pop('product_id__id')
            return cart_items
        except User.DoesNotExist:
            return []
        except Exception as e:
            raise ValueError(f"Django ORM summary error: {str(e)}")

    @staticmethod
    def get_cart_count(uid):
        """Get total item count in cart"""
        try:
            user = User.objects.get(id=uid)
            result = Cart.objects.filter(user_id=user, product_id__is_active=True).aggregate(
                total=Sum('quantity')
            )
            return result['total'] or 0
        except User.DoesNotExist:
            return 0
        except Exception as e:
            raise ValueError(f"Django ORM count error: {str(e)}")


def get_promo_code_details(promo_code: str):
    """Fetch promo code details using Django ORM."""
    try:
        promo = PromoCode.objects.filter(code=promo_code).first()
        if promo and promo.valid:
            return {"success": True, "discount": promo.discount}
        return {"success": False, "error": "Invalid or expired promo code"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_products_by_ids(product_ids):
    """Fetch products using Django ORM by their IDs and convert image URLs to public URLs."""
    products_qs = Product.objects.filter(id__in=product_ids)
    products = []
    for product in products_qs:
        # Build a dictionary for the product data
        product_data = {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "price": product.price,
            "original_price": product.original_price,
            "description": product.description,
            # If you have additional fields, include them here as needed.
        }
        # Convert the main image URL to a public URL if it exists
        if product.image_url:
            product_data["image_url"] = supabase.storage.from_(
                "product-image").get_public_url(product.image_url)
        else:
            product_data["image_url"] = None

        products.append(product_data)

    return products


def create_order(user_id, total_price, payment_method, address_data, shipping, discount):
    """
    Create an Order record using Django ORM.
    The address_data is serialized to JSON for storage.
    """
    try:
        # Get the user instance.
        user = User.objects.get(id=user_id)

        # Create the order.
        order = Order.objects.create(
            user_id=user,  # Assuming Order has a ForeignKey field 'user'
            total_price=total_price,
            payment_method=payment_method,
            # Storing address as a JSON string
            address=json.dumps(address_data),
            status="pending",
            shipping_rate=shipping,
            discount_rate=discount,
        )
        print("🔹 Order created:", order)
        return order.id, None
    except Exception as e:
        print("❌ Order creation failed:", str(e))
        return None, "Order creation failed"


def create_order_items(order_id, cart):
    """
    Create OrderItem records for each cart entry.
    The cart argument is expected to be a dictionary where each key is a product ID
    (as a string) and the value is a dictionary containing item details.
    """
    try:
        # Retrieve the order instance.
        order = Order.objects.get(id=order_id)

        # Loop over the cart and create an OrderItem for each product.
        for product_id, item in cart.items():
            product_id = int(product_id)
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                print(f"❌ Product with ID {product_id} not found; skipping.")
                continue

            # Check if sufficient stock exists.
            requested_qty = int(item.get("quantity", 1))
            if requested_qty > product.stock:
                print(
                    f"❌ Insufficient stock for {product.name}; skipping item.")
                continue

            OrderItem.objects.create(
                order_id=order,             # Use the field name from the model
                product_id=product,         # Use the field name from the model
                name=item.get("name"),
                # Assuming price is stored as Decimal
                price=item.get("price"),
                quantity=requested_qty,
                total_price=requested_qty * item.get("price")
            )

            # Deduct the ordered quantity from product stock.
            product.stock -= requested_qty
            product.save()

        print("✅ Order Items created successfully.")
        return None
    except Exception as e:
        print("❌ Exception in create_order_items:", str(e))
        traceback.print_exc()
        return str(e)


def delete_order(order_id):
    """
    Delete the specified Order record using Django ORM.
    """
    try:
        order = Order.objects.get(id=order_id)
        order.delete()
        print(f"✅ Order ID {order_id} deleted successfully.")
        return None
    except Order.DoesNotExist:
        print(f"❌ Order ID {order_id} does not exist.")
        return "Order does not exist"
    except Exception as e:
        print("❌ Exception in delete_order:", str(e))
        return str(e)


def delete_purchased_products(product_ids):
    """
    Mark purchased products as inactive and remove them from all users' carts.
    Expects product_ids as a list of IDs.
    """
    if not isinstance(product_ids, list):
        print("❌ Error: Expected list of product IDs, got", type(product_ids))
        return "Invalid product IDs format"

    try:
        # Convert IDs to integers, filtering out any non-numeric values.
        product_ids = [int(pid) for pid in product_ids if str(pid).isdigit()]
        if not product_ids:
            print("❌ Error: No valid product IDs provided")
            return "No products to delete"

        print("🛑 Marking products as inactive:", product_ids)

        # Only mark products as inactive if their stock is 0.
        updated_count = Product.objects.filter(
            id__in=product_ids,
            stock=0
        ).update(is_active=False)
        print(f"✅ Marked {updated_count} products as inactive (stock 0)")

        # Delete corresponding entries from the Cart.
        deleted_count, _ = Cart.objects.filter(
            product_id__in=product_ids).delete()
        print(f"✅ Deleted {deleted_count} cart entries")
        return None  # Success
    except Exception as e:
        print("❌ Exception in delete_purchased_products:", str(e))
        return "Error processing products"


def get_user_email(user_id):
    try:
        user = User.objects.get(id=user_id)
        if not user.email or "@" not in user.email:
            print(f"❌ Invalid email format for user {user_id}: {user.email}")
            return None
        return user.email
    except ObjectDoesNotExist:
        print(f"❌ No user found with ID: {user_id}")
        return None
    except Exception as e:
        print(f"🚨 Error fetching user email: {str(e)}")
        return None


def get_order_by_id(order_id: int) -> Order:
    try:
        return Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return None


def update_order_status(order_id: int, status: str) -> bool:
    try:
        order = Order.objects.get(id=order_id)
        order.status = status
        order.save()
        return True
    except Order.DoesNotExist:
        return False


def get_order_items(order_id):
    try:
        order = Order.objects.get(id=order_id)
        return [item.product_id.id for item in order.items.all()]
    except Order.DoesNotExist:
        return []


def get_all_orders():
    orders = Order.objects.all()
    result = []
    for order in orders:
        order_data = {
            'id': order.id,
            'user_id': order.user_id.id,
            'total_price': order.total_price,
            'status': order.status,
            'created_at': order.created_at,
            'items': [item.product_id.id for item in order.items.all()]
        }
        result.append(order_data)
    return result

# def get_order_items_with_details(order_id):
#     try:
#         order = Order.objects.get(id=order_id)
#         items = OrderItem.objects.filter(order_id=order).select_related('product_id')
#         return [{
#             "id": item.id,
#             "product_id": item.product_id.id,
#             "product_name": item.product_id.name,
#             "quantity": item.quantity,
#             "price": item.price
#         } for item in items]
#     except Order.DoesNotExist:
#         return []


def get_order_items_with_details(order_id):
    """Fetch order items with product details including images."""
    try:
        order_items = OrderItem.objects.filter(
            order_id=order_id).select_related('product_id')
        items_data = []
        for item in order_items:
            # Note: this might be None if using SET_NULL, but here we rely on soft deletion
            product = item.product_id

            if product and not product.is_deleted:
                main_image_url = (
                    supabase.storage.from_(
                        "product-image").get_public_url(product.image_url)
                    if product.image_url else None
                )
                additional_images = [
                    supabase.storage.from_(
                        "product-image").get_public_url(getattr(product, field))
                    for field in ["image_url2", "image_url3", "image_url4"]
                    if getattr(product, field, None)
                ]
                product_name = product.name
            else:
                # If the product is soft-deleted, show fallback details.
                main_image_url = None
                additional_images = []
                product_name = "Product no longer available"

            items_data.append({
                "id": item.id,
                "product_id": product.id if product else None,
                "product_name": product_name,
                "quantity": item.quantity,
                "price": item.price,
                "total_price": item.total_price,
                "image_url": main_image_url,
                "additional_images": additional_images
            })

        return items_data

    except Order.DoesNotExist:
        return []


def get_user_orders(user_id):
    """Fetch orders for a user along with order items and product images."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return []

    orders = Order.objects.filter(user_id=user_id).order_by('-created_at')

    orders_data = []
    for order in orders:
        order_items = get_order_items_with_details(
            order.id)  # Fetch order items with images
        orders_data.append({
            "id": order.id,
            "created_at": order.created_at,
            "status": order.status,
            "total_price": order.total_price,
            "items": order_items
        })

    return orders_data


def extract_customer_name(address):
    if not address:
        return "Unknown"
    # If address is a string, convert it to a dict
    if isinstance(address, str):
        try:
            address = json.loads(address)
        except Exception as e:
            return "Unknown"
    return address.get("name", "Unknown")


def get_all_orders_for_admin():
    orders = Order.objects.all().order_by('-created_at')
    result = []
    for order in orders:
        items = get_order_items_with_details(order.id)
        total_items = sum(item['quantity'] for item in items) if items else 0

        created_date = order.created_at
        formatted_date = created_date.strftime(
            "%b %d, %Y at %I:%M %p") if created_date else "Unknown"

        complete_order = {
            "id": order.id,
            "user_id": order.user_id.id,
            "customer_name": extract_customer_name(order.address),
            "total_price": order.total_price,
            "status": order.status,
            "created_at": formatted_date,
            "address": order.address,
            "payment_method": order.payment_method,
            "items": items,
            "total_items": total_items
        }
        result.append(complete_order)
    return result

def create_admin_store_record(uid, company_logo, company_name, email, phone, shop_address, pincode):
    """
    Creates a new AdminStore record.
    The company_logo is uploaded to storage, and the public URL is saved in the record.
    """
    # Upload the logo image and get its public URL
    logo_url = upload_image(company_logo)

    # Create the AdminStore record with the public URL
    admin_record = AdminStore.objects.create(
        firebase_uid=uid,
        company_logo=logo_url,  # Store the public URL instead of the file object
        company_name=company_name,
        email=email,
        phone=phone,
        shop_address=shop_address,
        pincode=pincode,
    )
    return admin_record

def get_public_logo_url(admin_record):
    """
    Returns the public URL for the company logo if available.
    """
    if admin_record.company_logo:
        return admin_record.company_logo.url
    return None