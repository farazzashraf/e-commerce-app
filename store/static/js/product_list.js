// Function to update the cart count from the server
function updateCartCount() {
    fetch('/cart_count/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'  // Include cookies automatically
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

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}

function addToCart(event) {
    const button = event.target;
    const productCard = button.closest('.product-card');

    if (!productCard) {
        console.error("Product card not found!");
        return;
    }

    const productId = productCard.dataset.productId;
    const productName = productCard.querySelector('h3')?.textContent || "Unknown";
    const productCategory = productCard.querySelector('.category')?.textContent.replace('Category: ', '') || "Uncategorized"; // ✅ Fetch category
    const productPrice = parseFloat(productCard.querySelector('.price')?.textContent.replace('₹', '') || "0");
    const productImage = productCard.querySelector('img')?.src || "";
    const productQuantity = parseInt(productCard.querySelector('.qty-display')?.textContent || "1");

    console.log(`Adding to cart: ${productName}, Category: ${productCategory}, Qty: ${productQuantity}`);

    fetch('/add_to_cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            product_id: productId,
            name: productName,
            category: productCategory,  // ✅ Added category
            price: productPrice,
            image_url: productImage,
            quantity: productQuantity
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartCount();
                document.dispatchEvent(new Event('cart-updated')); // Notify other scripts
            } else {
                console.error("Failed to add product to cart", data.error);
            }
        })
        .catch(error => console.error("Error:", error));
}

// Function to reset all quantity displays to 1
function resetQuantities() {
    const qtyDisplays = document.querySelectorAll('.qty-display');
    qtyDisplays.forEach(qtyDisplay => {
        qtyDisplay.textContent = '1';  // Reset quantity to 1
    });
}

// Update Quantity Dynamically
function changeQuantity(event, increment) {
    const qtyDisplay = event.target.closest('.quantity')?.querySelector('.qty-display');
    if (!qtyDisplay) return;

    let currentQty = parseInt(qtyDisplay.textContent || "1");
    const newQty = increment ? currentQty + 1 : Math.max(1, currentQty - 1);

    qtyDisplay.textContent = newQty;
}


// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Reset quantities to 1 on page load
    resetQuantities();

    document.addEventListener('click', function (event) {
        if (event.target.classList.contains('add-to-cart')) {
            addToCart(event);
        } else if (event.target.classList.contains('increase')) {
            changeQuantity(event, true);
        } else if (event.target.classList.contains('decrease')) {
            changeQuantity(event, false);
        }
    });

    updateCartCount();
});

// Reset quantities on pageshow event to handle back navigation
window.addEventListener('pageshow', (event) => {
    if (event.persisted || (window.performance && window.performance.navigation.type === 2)) {
        resetQuantities();  // Reset quantities when navigating back to the page
    }
});