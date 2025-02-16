from django.urls import path
from .views import home, cart_view, add_to_cart, login_view, signup_view
from .auth_views import login_redirect, protected_view, logout_view


urlpatterns = [
    path('', home, name='home'),  # Map root URL to home view
    path('cart/', cart_view, name='cart'),
    path('add-to-cart/', add_to_cart, name='add_to_cart'),
    path('', login_view, name="login"),
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path('login-redirect/', login_redirect, name='login_redirect'),
    path('protected/', protected_view, name='protected_view'),
    path('logout/', logout_view, name='logout_view'),
]
