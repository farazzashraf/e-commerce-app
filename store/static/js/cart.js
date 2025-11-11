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
                    <p class="seller-details">Store: ${product.seller_name}</p>

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
            let discount = sessionStorage.getItem("discount") || 0;
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
                // Check if the error message indicates stock limit reached
                if (data.error && data.error.includes("exceeds available stock")) {
                    showToast("You've reached the maximum available stock for this product.");
                } else {
                    showToast("Error updating cart quantity.");
                }
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

function showToast(message) {
    const toast = document.getElementById("toast-message");
    toast.textContent = message;
    toast.style.display = "block";

    setTimeout(() => {
        toast.style.display = "none";
    }, 3000); // Hide after 3 seconds
}


function applyPromoCode() {
    const promoCode = document.getElementById("promo-code").value.trim();

    if (!promoCode) {
        showToast("Please enter a promo code.");
        return;
    }

    fetch("/apply_promo/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({ promo_code: promoCode }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                sessionStorage.setItem("discount", data.discount);
                document.querySelector(".summary-item.discount span:last-child").textContent = `-₹${data.discount}`;

                // ✅ Show Cancel Button
                document.getElementById("cancel-promo-btn").style.display = "inline-block";

                // ✅ Show Success Message
                showToast("Promo code applied successfully!");

                loadCart();
            } else {
                showToast(data.error);
            }
        })
        .catch(error => console.error("Error:", error));
}



document.addEventListener("DOMContentLoaded", function () {
    const promoInput = document.getElementById("promo-code");
    const applyButton = document.getElementById("apply-promo-btn");
    const cancelButton = document.getElementById("cancel-promo-btn");

    if (applyButton) {
        applyButton.addEventListener("click", applyPromoCode);
    }

    if (cancelButton) {
        cancelButton.addEventListener("click", cancelPromoCode);
    }

    // ✅ Trigger applyPromoCode() when Enter key is pressed inside promo code input
    if (promoInput) {
        promoInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault(); // Prevent form submission (if any)
                applyPromoCode();
            }
        });
    }

    // ✅ Check if promo code is already applied (on page load)
    const savedDiscount = sessionStorage.getItem("discount");
    const savedPromoCode = sessionStorage.getItem("appliedPromoCode"); // Store applied promo code

    if (savedDiscount && savedDiscount !== "0") {
        document.querySelector(".summary-item.discount span:last-child").textContent = `-₹${savedDiscount}`;
        promoInput.value = savedPromoCode; // ✅ Restore the applied promo code
        cancelButton.style.display = "block"; // ✅ Ensure cancel button is visible
    }
});


function cancelPromoCode() {
    sessionStorage.removeItem("discount");
    document.querySelector('.summary-item.discount span:last-child').textContent = "-₹0";

    // ✅ Hide Cancel Button
    document.getElementById("cancel-promo-btn").style.display = "none";

    // ✅ Clear Promo Code Input Field
    document.getElementById("promo-code").value = "";

    // ✅ Show Message
    showToast("Promo code removed.");

    loadCart();
}


document.addEventListener("DOMContentLoaded", function () {
    // Safe promo code application
    const applyPromoBtn = document.querySelector('#apply-promo-btn');
    const cancelPromoBtn = document.querySelector('#cancel-promo-btn');

    if (applyPromoBtn) {
        applyPromoBtn.addEventListener('click', function (event) {
            event.preventDefault();
            try {
                applyPromoCode();
            } catch (error) {
                console.error('Error applying promo code:', error);
            }
        });
    }

    if (cancelPromoBtn) {
        cancelPromoBtn.addEventListener('click', function (event) {
            event.preventDefault();
            try {
                cancelPromoCode();
            } catch (error) {
                console.error('Error canceling promo code:', error);
            }
        });
    }

    const checkoutButton = document.querySelector('.checkout-btn');

    if (checkoutButton) {
        checkoutButton.addEventListener('click', function (event) {
            event.preventDefault(); // Prevent default action

            // Check if cart has items
            const cartItems = document.querySelectorAll('.cart-item');

            if (cartItems.length === 0) {
                alert('Your cart is empty. Please add items before checkout.');
                return;
            }

            let discount = sessionStorage.getItem("discount") || 0;
            let shipping = 99;

            // Redirect to checkout with discount and shipping applied
            window.location.href = `/checkout/?discount=${discount}&shipping=${shipping}`;
        });
    }
});

window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        // Clear promo code and discount when navigating back to cart
        localStorage.removeItem("discount");
        localStorage.removeItem("appliedPromoCode");
    }
});

window.addEventListener("beforeunload", function () {
    // Clear promo code when user leaves the page
    localStorage.removeItem("discount");
    localStorage.removeItem("appliedPromoCode");
});
