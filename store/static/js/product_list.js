class ShoppingCart {
    constructor() {
        this.cartCount = 0;
        this.csrfToken = this.getCookie('csrftoken');
        this.modalTimeout = null;
    }

    // Get CSRF token from cookies
    getCookie(name) {
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

    // Update cart count from server
    updateCartCount() {
        fetch('/cart_count/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                this.cartCount = data.cart_count || 0;
                this.updateCartCountDisplay();
            })
            .catch(error => {
                console.error('Error updating cart count:', error);
                // Fallback to local cart count if server request fails
                this.updateCartCountDisplay();
            });
    }

    // Update cart count display
    updateCartCountDisplay() {
        const cartCountElements = document.querySelectorAll('.cart-count');
        cartCountElements.forEach(element => {
            element.textContent = this.cartCount;

            // Add animation class
            element.classList.add('pulse');
            setTimeout(() => {
                element.classList.remove('pulse');
            }, 500);
        });
    }

    // Show modal with product info
    showAddedToCartModal(productName) {
        const modal = document.getElementById('cart-modal');
        const modalTitle = modal.querySelector('h3');
        const modalContent = modal.querySelector('p');

        // Update modal content
        modalTitle.textContent = 'Item Added to Cart!';
        modalContent.textContent = `${productName} has been added to your shopping cart.`;

        // Show modal
        modal.classList.add('active');

        // Clear any existing timeout
        if (this.modalTimeout) {
            clearTimeout(this.modalTimeout);
        }

        // Auto-hide after 3 seconds
        this.modalTimeout = setTimeout(() => {
            modal.classList.remove('active');
        }, 3000);
    }

    // In ShoppingCart class
    showStockError(message) {
        const modal = document.getElementById('cart-modal');
        modal.querySelector('h3').innerHTML = '<i class="fas fa-exclamation-triangle"></i> Stock Limit';
        modal.querySelector('p').textContent = message;
        modal.classList.add('stock-error');
        modal.classList.add('active');

        if (this.modalTimeout) clearTimeout(this.modalTimeout);
        this.modalTimeout = setTimeout(() => {
            modal.classList.remove('active');
            modal.classList.remove('stock-error');
        }, 5000);
    }

    // Add product to cart
    addToCart(productCard) {
        if (!productCard) {
            console.error("Product card not found!");
            return;
        }

        // Get product details
        const productId = productCard.dataset.productId;
        const productName = productCard.querySelector('h3')?.textContent || "Unknown";
        const productCategory = productCard.querySelector('.category')?.textContent || "Uncategorized";
        // const priceText = productCard.querySelector('.price')?.textContent || "₹0";
        // const productPrice = parseFloat(priceText.replace('₹', '').split(' ')[0]);
        const productPrice = parseFloat(productCard.querySelector('.price')?.textContent.replace('₹', '') || "0");
        const productImage = productCard.querySelector('img')?.src || "";
        const productQuantity = parseInt(productCard.querySelector('.qty-display')?.textContent || "1");

        console.log(`Adding to cart: ${productName}, Category: ${productCategory}, Qty: ${productQuantity}, Price: ${productPrice}`);

        // Show loading state
        const addButton = productCard.querySelector('.add-to-cart');
        const originalText = addButton.innerHTML;
        addButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        addButton.disabled = true;

        // Send request to server
        fetch('/add_to_cart/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                product_id: productId,
                name: productName,
                category: productCategory,
                price: productPrice,
                image_url: productImage,
                quantity: productQuantity
            })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Increment cart count
                    this.cartCount += productQuantity;
                    this.updateCartCountDisplay();

                    // Show success modal
                    this.showAddedToCartModal(productName);

                    // Reset quantity
                    productCard.querySelector('.qty-display').textContent = '1';

                    // Dispatch event for other components
                    document.dispatchEvent(new CustomEvent('cart-updated', {
                        detail: {
                            product: {
                                id: productId,
                                name: productName,
                                price: productPrice,
                                quantity: productQuantity
                            }
                        }
                    }));
                } else {
                    if (data.error.includes('available') || data.error.includes('add')) {
                        this.showStockError(data.error);
                    } else {
                        this.showError(data.error);
                    }
                }
            })
            .catch(error => {
                console.error("Error:", error);
                this.showError("Network error. Please try again.");
            })
            .finally(() => {
                // Restore button state
                addButton.innerHTML = originalText;
                addButton.disabled = false;
            });
    }

    // Show error message
    showError(message) {
        const modal = document.getElementById('cart-modal');
        const modalTitle = modal.querySelector('h3');
        const modalContent = modal.querySelector('p');

        modalTitle.textContent = 'Oops! Something went wrong';
        modalContent.textContent = message;

        modal.classList.add('active');

        if (this.modalTimeout) {
            clearTimeout(this.modalTimeout);
        }

        this.modalTimeout = setTimeout(() => {
            modal.classList.remove('active');
        }, 3000);
    }
}

// ============ Product Listing Functionality ============
class ProductListing {
    constructor(cart) {
        this.cart = cart;
        this.initEventListeners();
    }

    // Initialize event listeners
    initEventListeners() {
        // Use event delegation for better performance
        document.addEventListener('click', (event) => {
            // Add to cart button
            if (event.target.closest('.add-to-cart')) {
                const button = event.target.closest('.add-to-cart');
                const productCard = button.closest('.product-card');
                this.cart.addToCart(productCard);
            }

            else if (event.target.closest('.increase')) {
                const button = event.target.closest('.increase');
                const qtyDisplay = button.parentNode.querySelector('.qty-display');
                let currentQty = parseInt(qtyDisplay.textContent, 10) || 1;
                qtyDisplay.textContent = (currentQty + 1).toString();
            }

            // Decrease quantity button
            else if (event.target.closest('.decrease')) {
                const button = event.target.closest('.decrease');
                const qtyDisplay = button.parentNode.querySelector('.qty-display');
                let currentQty = parseInt(qtyDisplay.textContent, 10) || 1;
                if (currentQty > 1) {
                    qtyDisplay.textContent = (currentQty - 1).toString();
                }
            }


            // Wishlist button
            else if (event.target.closest('.wishlist-btn')) {
                const button = event.target.closest('.wishlist-btn');
                const icon = button.querySelector('i');

                if (icon.classList.contains('far')) {
                    icon.classList.replace('far', 'fas');
                    icon.style.color = '#ff5733';
                } else {
                    icon.classList.replace('fas', 'far');
                    icon.style.color = '';
                }
            }

            // Filter buttons
            else if (event.target.closest('.filter-button')) {
                const button = event.target.closest('.filter-button');
                document.querySelectorAll('.filter-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                button.classList.add('active');

                // Backend filtering: Redirect to the filtered product page
                const category = button.textContent.trim();
                window.location.href = `/?category=${encodeURIComponent(category)}`;

                // this.filterProducts(button.textContent.trim());
            }

            // Modal close button
            else if (event.target.closest('.modal-close')) {
                document.getElementById('cart-modal').classList.remove('active');
            }

            // Continue shopping button
            else if (event.target.closest('.secondary-button')) {
                document.getElementById('cart-modal').classList.remove('active');
            }

            // View cart button
            else if (event.target.closest('.primary-button')) {
                window.location.href = '/cart_view/';
            }

            // Sticky cart button
            else if (event.target.closest('.sticky-cart-btn')) {
                window.location.href = '/cart_view/';
            }
        });

        // Sort dropdown
        const sortDropdown = document.getElementById('sort-options');
        if (sortDropdown) {
            sortDropdown.addEventListener('change', () => {
                this.sortProducts(sortDropdown.value);
            });
        }
    }

    // Reset quantities
    resetQuantities() {
        document.querySelectorAll('.qty-display').forEach(display => {
            display.textContent = '1';
        });
    }

    // Simulate loading for demonstration
    simulateLoading() {
        const productGrid = document.querySelector('.product-grid');
        const loader = document.querySelector('.loader');

        if (productGrid && loader) {
            productGrid.style.display = 'none';
            loader.style.display = 'block';

            setTimeout(() => {
                loader.style.display = 'none';
                productGrid.style.display = 'grid';
            }, 800);
        }
    }

    // Filter products - placeholder for actual implementation
    filterProducts(category) {
        console.log(`Filtering by: ${category}`);
        this.simulateLoading();

        // In a real application, you would fetch filtered products from the server
        // or filter the current products in the DOM
    }

    // Sort products - placeholder for actual implementation
    sortProducts(sortOption) {
        console.log(`Sorting by: ${sortOption}`);
        this.simulateLoading();

        // In a real application, you would fetch sorted products from the server
        // or sort the current products in the DOM
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const cart = new ShoppingCart();
    const productListing = new ProductListing(cart);

    // Reset quantities
    productListing.resetQuantities();

    // Initial cart count update
    cart.updateCartCount();

    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.2); }
            100% { transform: scale(1); }
        }
        .pulse {
            animation: pulse 0.5s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .product-card {
            animation: fadeIn 0.5s;
        }
    `;
    document.head.appendChild(style);
});

// Handle back navigation
window.addEventListener('pageshow', (event) => {
    if (event.persisted || (window.performance && window.performance.navigation.type === 2)) {
        document.querySelectorAll('.qty-display').forEach(display => {
            display.textContent = '1';
        });

        const cart = new ShoppingCart();
        cart.updateCartCount();
    }
});

document.addEventListener('DOMContentLoaded', function () {
    // Open overlay when "View Details" is clicked
    const viewButtons = document.querySelectorAll('.view-details');
    const overlay = document.getElementById('product-overlay'); // Get the global overlay

    viewButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.stopPropagation();
            const card = this.closest('.product-card');

            // Update overlay content dynamically
            const productTitle = card.querySelector('h3').textContent;
            const productCategory = card.querySelector('.category').textContent;
            const productDescription = card.querySelector('.description').textContent;
            const productPrice = card.querySelector('.current-price').textContent;
            const productImage = card.querySelector('img').src;

            document.querySelector('.product-title').textContent = productTitle;
            document.querySelector('.product-category').textContent = productCategory;
            document.querySelector('.product-description').textContent = productDescription;
            document.querySelector('.product-current-price').textContent = productPrice;
            document.getElementById('main-product-image').src = productImage;

            // Show the overlay
            overlay.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Prevent scrolling
        });
    });

    // Close overlay when the close button is clicked
    document.querySelector('.close-overlay').addEventListener('click', function () {
        overlay.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
    });


    // Close overlay when clicking outside the content
    const overlays = document.querySelectorAll('.product-overlay');
    overlays.forEach(overlay => {
        overlay.addEventListener('click', function (e) {
            if (e.target === this) {
                this.style.display = 'none';
                document.body.style.overflow = 'auto'; // Re-enable scrolling
            }
        });
    });
});

// document.addEventListener("DOMContentLoaded", function () {
//     document.querySelectorAll(".product-card").forEach((productCard) => {
//         let productId = productCard.getAttribute("data-product-id");
//         let dateAdded = productCard.getAttribute("data-added");

//         if (!dateAdded || dateAdded === "N/A") {
//             console.error(`❌ Missing Date for Product ID: ${productId}`);
//         } else {
//             console.log(`✅ Product ID: ${productId}, Date Added: ${dateAdded}`);
//         }

//         // Debugging: Add visible text to the page
//         // productCard.innerHTML += `<p><strong>Date Added:</strong> ${dateAdded}</p>`;
//     });
// });