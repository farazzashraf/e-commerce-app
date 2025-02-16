from django.contrib import admin
from django.urls import path, include  # Ensure `include` is imported

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),  # Include store app URLs
]