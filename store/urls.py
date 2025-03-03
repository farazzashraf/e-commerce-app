from django.urls import path, include
from .views import home, cart_view, add_to_cart, login_view, signup_view, firebase_auth, logout_view, check_email, cart_count
from .views import update_cart, admin_dashboard, admin_login, admin_logout, add_product_view, delete_product_view, remove_from_cart
from .views import update_product_view, apply_promo_code
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("home/", home, name="home"),
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path('check-email/', check_email, name='check_email'),
    path("logout/", logout_view, name="logout"),  # ✅ Added missing `/`
    path("firebase-auth/", firebase_auth, name="firebase_auth"),  # ✅ Added missing `/`
    path("cart_view/", cart_view, name="cart_view"),
    path("add_to_cart/", add_to_cart, name="add_to_cart"),
    path("cart_count/", cart_count, name="cart_count"),
    path("update_cart/", update_cart, name="update_cart"),
    path('store-admin/login/', admin_login, name='admin_login'),
    path('store-admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('store-admin/add-product/', add_product_view, name='add_product_view'),
    path('store-admin/logout/', admin_logout, name='admin_logout'),
    path("store-admin/delete-product/<int:product_id>/", delete_product_view, name="delete_product"),
    path("store-admin/admin_update/<int:product_id>/", update_product_view, name="admin_update"),  # ✅ Added update product URL
    path('update_cart/', update_cart, name='update_cart'),
    path('remove_from_cart/', remove_from_cart, name='remove_from_cart'),  # ✅ Add this
    path('apply_promo_code/', apply_promo_code, name='apply_promo_code'),  # ✅ Add this
    


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)