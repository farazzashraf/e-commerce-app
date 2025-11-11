from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from store.views import (
    home, cart_view, add_to_cart, login_view, signup_view, firebase_auth, logout_view, check_email, cart_count,
    update_cart, admin_dashboard, admin_login, add_product_view, delete_product_view, remove_from_cart,
    update_product_view, check_login_status, api_products, update_verification, about_us, apply_promo, checkout, admin_approve_order,
    place_order, order_success, admin_orders, order_details, admin_analysis, orders_view, cancel_order, help_support,
    update_stock, admin_signup, get_subcategories, get_categories, seller_page, seller_details, seller_product_details,
    seller_order_analytics, admin_products, restock_product, toggle_product_status, admin_logout  # Import the new place_order view
)
# from django.contrib import admin

urlpatterns = [
    path("check-login-status/", check_login_status, name="check_login_status"),
    path("", home, name="home"),
    path('about_us/', about_us, name='about_us'),
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path('check-email/', check_email, name='check_email'),
    path("logout/", logout_view, name="logout"),  # ✅ Added missing `/`
    path("firebase-auth/", firebase_auth,
         name="firebase_auth"),  # ✅ Added missing `/`
    path("cart_view/", cart_view, name="cart_view"),
    path("add_to_cart/", add_to_cart, name="add_to_cart"),
    path("cart_count/", cart_count, name="cart_count"),
    path("update_cart/", update_cart, name="update_cart"),
    path('apply_promo/', apply_promo, name='apply_promo'),
    path('update_cart/', update_cart, name='update_cart'),
    path('remove_from_cart/', remove_from_cart,
         name='remove_from_cart'),  # ✅ Add this
    path('store-admin/add-product/', add_product_view, name='add_product'),
    # path('store-admin/logout/', admin_logout, name='admin_logout'),
    path("store-admin/delete-product/<int:product_id>/",
         delete_product_view, name="delete_product"),
    path("store-admin/admin_update/<int:product_id>/", update_product_view,
         name="admin_update"),  # ✅ Added update product URL
    path('api/products/', api_products, name='api_products'),
    path('update_verification/', update_verification, name='update_verification'),
    path('checkout/', checkout, name='checkout'),
    path("place-order/", place_order, name="place_order"),
    path("order-success/", order_success, name="order_success"),
    path('store-admin/orders/', admin_orders, name='admin_orders'),
    path('store-admin/order-details/<int:order_id>/',
         order_details, name='order_details'),
    path("store-admin/orders/approve/<int:order_id>/<str:action>/",
         admin_approve_order, name="admin_approve_order"),
    path('store-admin/analysis/', admin_analysis, name='admin_analysis'),
    path('orders/', orders_view, name='orders'),
    path('cancel_order/<int:order_id>/', cancel_order, name='cancel_order'),
    path('help_support/', help_support, name='help_support'),
    # path('update-stock/<int:product_id>/', update_stock, name='update_stock'),
    path('update-stock/', update_stock, name='update_stock'),
    path("admin-signup/", admin_signup, name="admin_signup"),
    # API endpoints for categories and products
    path('api/categories/', get_categories, name='api_categories'),
    path('api/categories/<int:category_id>/subcategories/',
         get_subcategories, name='api_subcategories'),
    path('seller_page', seller_page, name='seller_page'),
    path('seller/<uuid:adminstore_id>/', seller_details, name='seller_details'),
    path('product/<int:product_id>/', seller_product_details,
         name='seller_product_details'),
    path('api/seller-analytics/<uuid:admin_id>/',
         seller_order_analytics, name='seller_order_analytics'),
    path('store-admin/login/', admin_login, name='admin_login'),
    path('store-admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('store-admin/restock-product/', restock_product, name='restock_product'),
    path('store-admin/add-product/', add_product_view, name='add_product'),
    path("store-admin/admin_update/<int:product_id>/", update_product_view, name="admin_update"),  # ✅ Added update product URL
    # API endpoints for categories and products
    path('store-admin/admin_products/', admin_products, name='admin_products'),
    path('store-admin/toggle-product-status/<int:product_id>/', toggle_product_status, name='toggle_product_status'),
    path("store-admin/delete-product/<int:product_id>/", delete_product_view, name="delete_product"),
    path('store-admin/logout/', admin_logout, name='admin_logout'),
    
    


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# from django.urls import path
# from store.views import admin_views  # Import from store.views.admin_views

# urlpatterns = [
#     
# ]
