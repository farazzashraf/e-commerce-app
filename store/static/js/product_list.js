// product_list.js

// Function to update the cart count on the header
function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem('cart')) || {};
    const cartCount = Object.values(cart).reduce((acc, product) => acc + product.quantity, 0);
    document.querySelector('.cart-count').textContent = cartCount;
}

// Track the default quantity for reset
const initialQuantities = {};

// Save the initial quantity for each product when the page is first loaded
document.querySelectorAll('.product-card').forEach(card => {
    const productId = card.dataset.productId;
    const initialQty = parseInt(card.querySelector('.qty-display').textContent);
    initialQuantities[productId] = initialQty;
});

// Add event listeners for "Add to Cart" buttons
document.addEventListener('DOMContentLoaded', () => {
    const addToCartButtons = document.querySelectorAll('.add-to-cart');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            // Get the product details from the data attributes
            const productCard = this.closest('.product-card');
            const productId = productCard.dataset.productId;
            const productName = productCard.querySelector('h3').textContent;
            const productSize = productCard.querySelector('.item-size').textContent;
            const productPrice = parseFloat(productCard.querySelector('.price').textContent.replace('₹', '').trim().replace(',', ''));
            const productQuantity = parseInt(productCard.querySelector('.qty-display').textContent);

            // Create a product object
            const product = {
                id: productId,
                name: productName,
                size: productSize,
                price: productPrice,
                quantity: productQuantity
            };

            // Get the current cart from localStorage
            let cart = JSON.parse(localStorage.getItem('cart')) || {};

            // If the product is already in the cart, update the quantity
            if (cart[productId]) {
                cart[productId].quantity += productQuantity;
            } else {
                // Otherwise, add the new product to the cart
                cart[productId] = product;
            }

            // Save the updated cart to localStorage
            localStorage.setItem('cart', JSON.stringify(cart));

            // Update the cart count in the header
            // updateCartCount();
            // Dispatch a custom event to notify the header to update the cart count
            const cartUpdatedEvent = new CustomEvent('cart-updated');
            document.dispatchEvent(cartUpdatedEvent);
        });
    });

    // Event listeners for quantity increase and decrease buttons
    const increaseButtons = document.querySelectorAll('.increase');
    const decreaseButtons = document.querySelectorAll('.decrease');

    increaseButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            const qtyDisplay = this.closest('.quantity').querySelector('.qty-display');
            let currentQty = parseInt(qtyDisplay.textContent);
            qtyDisplay.textContent = currentQty + 1;
        });
    });

    decreaseButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            const qtyDisplay = this.closest('.quantity').querySelector('.qty-display');
            let currentQty = parseInt(qtyDisplay.textContent);
            if (currentQty > 1) {
                qtyDisplay.textContent = currentQty - 1;
            }
        });
    });

    // Reset the quantity to the initial state when navigating back
    window.addEventListener('pageshow', () => {
        document.querySelectorAll('.product-card').forEach(card => {
            const productId = card.dataset.productId;
            const qtyDisplay = card.querySelector('.qty-display');
            qtyDisplay.textContent = initialQuantities[productId];
        });
    });

    // Initialize the cart count
    updateCartCount();
});
