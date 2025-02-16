# Remove this line: from .views import home
from django.shortcuts import render, redirect
from django.http import JsonResponse


def login_view(request):
    return render(request, "store/login.html")


def signup_view(request):
    return render(request, "store/signup.html")


def home(request):
    return render(request, 'store/home.html')


def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))

        # Get or initialize cart in session
        cart = request.session.get('cart', {})

        # Update cart quantity
        if product_id in cart:
            cart[product_id] += quantity
        else:
            cart[product_id] = quantity

        request.session['cart'] = cart
        return JsonResponse({
            'success': True,
            'cart_count': sum(cart.values())
        })

    return JsonResponse({'success': False}, status=400)


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    # This should be replaced with actual product data from MongoDB
    for product_id, quantity in cart.items():
        # Example product data - replace with your MongoDB query
        product = {
            'id': product_id,
            'name': f"Product {product_id}",
            'price': 1499,
            'image': f"product{product_id}.jpg"
        }

        cart_items.append({
            'product_id': product_id,
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity,
            'total': product['price'] * quantity
        })
        total_price += product['price'] * quantity

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': sum(cart.values())
    })


def cart_count(request):
    # Get the cart from the session
    cart = request.session.get('cart', {})
    # Sum the quantity of items in the cart
    cart_item_count = sum(cart.values())

    return JsonResponse({'cart_count': cart_item_count})

def save_last_page(request):
    request.session["last_page"] = request.path