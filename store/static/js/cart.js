document.addEventListener('DOMContentLoaded', () => {
    const cartContainer = document.querySelector('.cart-items');
    const cartSummary = document.querySelector('.cart-summary');

    if (!cartContainer || !cartSummary) {
        console.error('Cart container or summary not found!');
        return;
    }

    console.log('Cart container and summary loaded.');
    loadCart();

    function loadCart() {
        let cart = JSON.parse(localStorage.getItem('cart')) || {};
        cartContainer.innerHTML = ''; // Clear previous cart items

        let subtotal = 0;
        let itemCount = 0;

        Object.values(cart).forEach(product => {
            const cartItem = document.createElement('div');
            cartItem.classList.add('cart-item');
            cartItem.innerHTML = `
                <div class="item-image">
                    <img src="/static/images/product${product.id}.jpg" alt="${product.name}">
                </div>
                <div class="item-details">
                    <h3>${product.name}</h3>
                    <p class="item-size">${product.size}</p>
                    <p class="item-unit-price">Price per unit: ₹${product.price}</p> <!-- Correct price from product_list -->
                    <div class="quantity-controls">
                        <button class="quantity-btn decrease" data-id="${product.id}">
                            <i class="fas fa-minus"></i>
                        </button>
                        <span class="quantity">${product.quantity}</span>
                        <button class="quantity-btn increase" data-id="${product.id}">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                </div>
                <div class="item-price">
                    <p class="price">Total: ₹${(product.price * product.quantity).toFixed(2)}</p>
                    <button class="remove-item" data-id="${product.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            subtotal += product.price * product.quantity;
            itemCount += product.quantity;  // Add up the item count
            cartContainer.appendChild(cartItem);
        });

        // Update the item count dynamically
        const itemCountElement = document.querySelector('.item-count');
        if (itemCountElement) {
            itemCountElement.textContent = `${itemCount} Items`; // Update item count
        } else {
            console.error('Item count element not found!');
        }

        // Update the summary section if the elements exist
        const subtotalElement = cartSummary.querySelector('.summary-item .subtotal');
        if (subtotalElement) {
            subtotalElement.textContent = `₹${subtotal.toFixed(2)}`;
        } else {
            console.error('Subtotal element not found!');
        }

        let shipping = 99;
        let discount = 500;
        let total = subtotal + shipping - discount;

        const totalElement = cartSummary.querySelector('.total span:last-child');
        if (totalElement) {
            totalElement.textContent = `₹${total.toFixed(2)}`;
        } else {
            console.error('Total element not found!');
        }

        addCartEventListeners();
    }

    function addCartEventListeners() {
        document.querySelectorAll('.increase').forEach(button => {
            button.addEventListener('click', function () {
                let cart = JSON.parse(localStorage.getItem('cart')) || {};
                let id = this.dataset.id;
                if (cart[id]) {
                    cart[id].quantity += 1;
                    localStorage.setItem('cart', JSON.stringify(cart));
                    loadCart();  // Reload cart after modification
                }
            });
        });

        document.querySelectorAll('.decrease').forEach(button => {
            button.addEventListener('click', function () {
                let cart = JSON.parse(localStorage.getItem('cart')) || {};
                let id = this.dataset.id;
                if (cart[id] && cart[id].quantity > 1) {
                    cart[id].quantity -= 1;
                    localStorage.setItem('cart', JSON.stringify(cart));
                    loadCart();  // Reload cart after modification
                }
            });
        });

        document.querySelectorAll('.remove-item').forEach(button => {
            button.addEventListener('click', function () {
                let cart = JSON.parse(localStorage.getItem('cart')) || {};
                let id = this.dataset.id;
                delete cart[id];
                localStorage.setItem('cart', JSON.stringify(cart));
                loadCart();  // Reload cart after item is removed
            });
        });
    }
});
