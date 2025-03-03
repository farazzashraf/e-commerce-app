// function addCartEventListeners() {
//     const cartItemsContainer = document.querySelector('.cart-items');
//     if (!cartItemsContainer) {
//         console.error("Cart items container not found!");
//         return;
//     }

//     cartItemsContainer.addEventListener('click', function (event) {
//         const button = event.target.closest('.quantity-btn');
//         if (button) {
//             let productId = button.dataset.id;
//             let action = button.classList.contains('increase') ? 'increase' : 'decrease';
//             updateCartQuantity(productId, action);
//         }

//         const removeButton = event.target.closest('.remove-item');
//         if (removeButton) {
//             let productId = removeButton.dataset.id;
//             removeFromCart(productId);
//         }
//     });
// }

function addCartEventListeners() {
    const cartItemsContainer = document.querySelector('.cart-items');
    if (!cartItemsContainer) {
        console.error("Cart items container not found!");
        return;
    }

    cartItemsContainer.removeEventListener('click', handleCartClick);
    cartItemsContainer.addEventListener('click', handleCartClick);
}

function handleCartClick(event) {
    const button = event.target.closest('.quantity-btn');
    if (button) {
        let productId = button.dataset.id;
        let action = button.classList.contains('increase') ? 'increase' : 'decrease';
        updateCartQuantity(productId, action);
    }

    const removeButton = event.target.closest('.remove-item');
    if (removeButton) {
        let productId = removeButton.dataset.id;
        removeFromCart(productId);
    }
}

function loadCart() {
    fetch('/cart_view/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'include'
    })
        .then(response => response.json())
        .then(data => {
            console.log("Cart Data Received:", data);

            const cartContainer = document.querySelector('.cart-items');
            if (!cartContainer) {
                console.error("Cart container not found!");
                return;
            }

            if (!data.cart || Object.keys(data.cart).length === 0) {
                cartContainer.innerHTML = '<p>Your cart is empty.</p>';
                document.querySelector('.item-count').textContent = `0 Items`;
                document.querySelector('.subtotal').textContent = `₹0`;
                document.querySelector('.total span:last-child').textContent = `₹99`;
                return;
            }

            cartContainer.innerHTML = '';

            let subtotal = 0;
            let itemCount = 0;

            Object.keys(data.cart).forEach(key => {
                const product = data.cart[key];
                const cartItem = document.createElement('div');
                cartItem.classList.add('cart-item');
                cartItem.innerHTML = `
                <div class="item-image">
                    <img src="${product.image_url}" alt="${product.name}">
                </div>
                <div class="item-details">
                    <h3>${product.name}</h3>
                    <p class="item-category">${product.category}</p>
                    <p class="item-unit-price">Price: ₹${product.price}</p>
                    <div class="quantity-controls">
                        <button class="quantity-btn decrease" data-id="${key}">
                            <i class="fas fa-minus"></i>
                        </button>
                        <span class="quantity">${product.quantity}</span>
                        <button class="quantity-btn increase" data-id="${key}">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                </div>
                <div class="item-price">
                    <p class="price">Total: ₹${(product.price * product.quantity).toFixed(2)}</p>
                    <button class="remove-item" data-id="${key}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;

                subtotal += product.price * product.quantity;
                itemCount += product.quantity;
                cartContainer.appendChild(cartItem);
            });

            document.querySelector('.item-count').textContent = `${itemCount} Items`;
            document.querySelector('.subtotal').textContent = `₹${subtotal.toFixed(2)}`;

            let shipping = 99;
            let discount = localStorage.getItem("discount") || 0;
            let total = subtotal + shipping - discount;
            document.querySelector('.summary-item.discount span:last-child').textContent = `-₹${discount}`;
            document.querySelector('.total span:last-child').textContent = `₹${total.toFixed(2)}`;

            addCartEventListeners();
        })
        .catch(error => console.error('Error loading cart:', error));
}

document.addEventListener("DOMContentLoaded", function () {
    if (document.querySelector('.cart-items')) {
        loadCart();

        const cartItemsContainer = document.querySelector('.cart-items');
        cartItemsContainer.addEventListener('click', function (event) {
            const button = event.target.closest('.quantity-btn');
            if (button) {
                let productId = button.dataset.id;
                let action = button.classList.contains('increase') ? 'increase' : 'decrease';
                updateCartQuantity(productId, action);
            }

            const removeButton = event.target.closest('.remove-item');
            if (removeButton) {
                let productId = removeButton.dataset.id;
                removeFromCart(productId);
            }
        });

        const applyPromoButton = document.getElementById("apply-promo");
        const cancelPromoButton = document.getElementById("cancel-promo");

        if (applyPromoButton && cancelPromoButton) {
            applyPromoButton.addEventListener("click", applyPromoCode);
            cancelPromoButton.addEventListener("click", removePromoCode);

            const savedPromo = localStorage.getItem("promoCode");
            if (savedPromo) {
                document.getElementById("promo-input").value = savedPromo;
                document.getElementById("promo-input").disabled = true;
                applyPromoButton.style.display = "none";
                cancelPromoButton.style.display = "inline-block";
            }
        }
    } else {
        console.log("Not on cart page, skipping cart event listeners.");
    }
});

function updateCartCount() {
    fetch('/cart_count/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        const cartCountElement = document.querySelector('.cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = data.cart_count || 0;
        }
    })
    .catch(error => console.error('Error updating cart count:', error));
}

function updateCartQuantity(productId, action) {
    fetch('/update_cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ product_id: productId, action: action })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadCart();
                updateCartCount();
                document.dispatchEvent(new Event('cart-updated'));
            } else {
                console.error('Error updating cart:', data.error);
            }
        })
        .catch(error => console.error('Error:', error));
}

function removeFromCart(productId) {
    fetch('/remove_from_cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ product_id: productId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadCart();
            updateCartCount();
        } else {
            console.error("Error removing item:", data.error);
        }
    })
    .catch(error => console.error('Error:', error));
}

function getCSRFToken() {
    return document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
}

