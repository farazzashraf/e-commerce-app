// ============ Product Overlay Functionality ============
class ProductOverlay {
    constructor(cart) {
        this.cart = cart;
        this.overlay = document.getElementById('product-overlay');
        this.currentProductId = null;
        this.currentProduct = null;
        this.currentImageIndex = 0;
        this.productImages = [];
        this.initEventListeners();
    }

    // Initialize event listeners
    initEventListeners() {
        // Open overlay when "View Details" is clicked
        document.querySelectorAll('.view-details').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const card = button.closest('.product-card');
                this.openProductOverlay(card);
            });
        });

        // Close overlay when close button is clicked
        const closeButton = this.overlay.querySelector('.close-overlay');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                this.closeOverlay();
            });
        }

        // Close overlay when clicking outside the content
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.closeOverlay();
            }
        });

        // Tab navigation
        this.overlay.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                const tabId = button.dataset.tab;
                this.switchTab(tabId);
            });
        });

        // Image navigation
        const prevButton = this.overlay.querySelector('.image-nav-button.prev');
        const nextButton = this.overlay.querySelector('.image-nav-button.next');

        if (prevButton) {
            prevButton.addEventListener('click', () => {
                this.navigateImages('prev');
            });
        }

        if (nextButton) {
            nextButton.addEventListener('click', () => {
                this.navigateImages('next');
            });
        }

        // Quantity controls
        const decreaseBtn = this.overlay.querySelector('.quantity-btn.decrease');
        const increaseBtn = this.overlay.querySelector('.quantity-btn.increase');
        const quantityInput = this.overlay.querySelector('.quantity-input');

        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', () => {
                const currentValue = parseInt(quantityInput.value);
                if (currentValue > 1) {
                    quantityInput.value = currentValue - 1;
                }
            });
        }

        if (increaseBtn) {
            increaseBtn.addEventListener('click', () => {
                const currentValue = parseInt(quantityInput.value);
                quantityInput.value = currentValue + 1;
            });
        }

        // Add to cart button
        const addToCartBtn = this.overlay.querySelector('.add-to-cart-btn');
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', () => {
                if (this.currentProduct) {
                    const quantity = parseInt(this.overlay.querySelector('.quantity-input').value);
                    this.addToCartFromOverlay(quantity);
                }
            });
        }

        // Wishlist button
        const wishlistBtn = this.overlay.querySelector('.wishlist-btn');
        if (wishlistBtn) {
            wishlistBtn.addEventListener('click', () => {
                const icon = wishlistBtn.querySelector('i');

                if (icon.classList.contains('far')) {
                    icon.classList.replace('far', 'fas');
                    icon.style.color = '#ff5733';
                } else {
                    icon.classList.replace('fas', 'far');
                    icon.style.color = '';
                }
            });
        }

        // Thumbnail click
        this.overlay.querySelector('.thumbnail-container').addEventListener('click', (e) => {
            const thumbnail = e.target.closest('.thumbnail');
            if (thumbnail) {
                const index = parseInt(thumbnail.dataset.index);
                this.setActiveImage(index);
            }
        });
    }

    // Open product overlay with data from the product card
    openProductOverlay(productCard) {
        if (!productCard) {
            console.error("Product card not found!");
            return;
        }

        // Get product details
        this.currentProductId = productCard.dataset.productId;
        const productName = productCard.querySelector('h3')?.textContent || "Unknown Product";
        const productCategory = productCard.querySelector('.category')?.textContent || "Uncategorized";
        const originalPriceEl = productCard.querySelector('.original-price');
        const currentPriceEl = productCard.querySelector('.current-price') || productCard.querySelector('.price');

        let originalPrice = originalPriceEl ? originalPriceEl.textContent : null;
        let currentPrice = currentPriceEl ? currentPriceEl.textContent : "₹0";

        // Calculate discount percentage
        let discountPercentage = null;
        if (originalPrice) {
            const origPrice = parseFloat(originalPrice.replace('₹', '').trim());
            const currPrice = parseFloat(currentPrice.replace('₹', '').trim());
            discountPercentage = Math.round(((origPrice - currPrice) / origPrice) * 100);
        }

        // Get product description dynamically from a data attribute or from a child element
        let description = productCard.dataset.description;
        if (!description) {
            description = productCard.querySelector('.product-description')?.textContent ||
                "This premium product offers excellent quality and value.";
        }

        // === Updated image extraction logic ===
        let images = [];
        if (productCard.dataset.images) {
            // Split the comma-separated string and remove any empty values
            images = productCard.dataset.images.split(',')
                .map(url => url.trim())
                .filter(url => url !== "");
        }

        images = images.filter((url, index) => images.indexOf(url) == index)
        // Fallback: Use the first <img> src if no images are found in the data attribute
        if (images.length === 0) {
            const mainImage = productCard.querySelector('img')?.src || "";
            if (mainImage) images.push(mainImage);
        }


        this.productImages = images;

        // Get stock information from product card
        const stock = parseInt(productCard.dataset.stock) || 0;
        console.log("Product card stock:", productCard.dataset.stock, "Parsed stock:", stock);


        // Store current product data
        this.currentProduct = {
            id: this.currentProductId,
            name: productName,
            category: productCategory,
            originalPrice: originalPrice,
            currentPrice: currentPrice,
            discountPercentage: discountPercentage,
            description: description,
            images: this.productImages,
            stock: stock
        };

        // ✅ Update overlay content only if images exist
        if (this.productImages.length > 0) {
            this.updateOverlayContent();
        }

        // Show overlay
        this.overlay.style.display = 'flex';
        // this.overlay.classList.add('show');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    }
    // Update overlay content with product data
    updateOverlayContent() {
        if (!this.currentProduct) return;

        // Set product details
        this.overlay.querySelector('.product-title').textContent = this.currentProduct.name;
        this.overlay.querySelector('.product-category').textContent = this.currentProduct.category;

        // Set pricing
        const originalPriceEl = this.overlay.querySelector('.product-original-price');
        const currentPriceEl = this.overlay.querySelector('.product-current-price');
        const discountEl = this.overlay.querySelector('.product-discount-percentage');

        if (this.currentProduct.originalPrice && this.currentProduct.discountPercentage) {
            originalPriceEl.textContent = this.currentProduct.originalPrice;
            originalPriceEl.style.display = 'inline-block';
            discountEl.textContent = `-${this.currentProduct.discountPercentage}%`;
            discountEl.style.display = 'inline-block';
        } else {
            originalPriceEl.style.display = 'none';
            discountEl.style.display = 'none';
        }

        currentPriceEl.textContent = this.currentProduct.currentPrice;

        // Set description
        this.overlay.querySelector('.product-description').textContent = this.currentProduct.description;

        // Reset quantity
        this.overlay.querySelector('.quantity-input').value = 1;

        const stockElement = this.overlay.querySelector('.stock-quantity');
        const metaItem = stockElement.closest('.meta-item');
        const addToCartBtn = this.overlay.querySelector('.add-to-cart-btn');

        console.log("Setting stock quantity:", this.currentProduct.stock);
        stockElement.textContent = `${this.currentProduct.stock} in stock`;
        console.log("Stock element after setting:", stockElement.textContent);

        console.log("Stock element exists:", stockElement !== null);
        console.log("Stock element display style:", window.getComputedStyle(stockElement).display);

        if (this.currentProduct.stock > 0) {
            stockElement.textContent = `${this.currentProduct.stock} in stock`;
            metaItem.classList.remove('out-of-stock', 'low-stock');

            if (this.currentProduct.stock < 5) {
                metaItem.classList.add('low-stock');
                stockElement.textContent += ' (Low Stock)';
            }

            addToCartBtn.disabled = false;
        } else {
            stockElement.textContent = 'Out of Stock';
            metaItem.classList.add('out-of-stock');
            addToCartBtn.disabled = true;
        }


        // Update badges
        const newBadge = this.overlay.querySelector('.new-badge');
        const saleBadge = this.overlay.querySelector('.sale-badge');

        // In a real app, this logic would be based on actual product data
        newBadge.style.display = Math.random() > 0.5 ? 'inline-block' : 'none';
        saleBadge.style.display = this.currentProduct.discountPercentage ? 'inline-block' : 'none';

        // Set main image and thumbnails
        this.currentImageIndex = 0;
        this.updateImageGallery();

        // Set tab content
        this.overlay.querySelector('#details-panel p').textContent = this.currentProduct.description;

        // Set initial active tab
        this.switchTab('details');
    }

    // ✅ Fix: Update Image Gallery Properly
    updateImageGallery() {
        if (!this.productImages.length) return;

        // Set main image
        const mainImageEl = this.overlay.querySelector('.main-image');
        if (mainImageEl) {
            mainImageEl.src = this.productImages[this.currentImageIndex];
            mainImageEl.alt = this.currentProduct.name;
        }

        // Generate thumbnails dynamically
        const thumbnailContainer = this.overlay.querySelector('.thumbnail-container');
        if (thumbnailContainer) {
            thumbnailContainer.innerHTML = ''; // Clear existing thumbnails

            this.productImages.forEach((img, index) => {
                const thumbnail = document.createElement('div');
                thumbnail.className = `thumbnail ${index === this.currentImageIndex ? 'active' : ''}`;
                thumbnail.dataset.index = index;

                const imgEl = document.createElement('img');
                imgEl.src = img;
                imgEl.alt = `${this.currentProduct.name} - View ${index + 1}`;

                thumbnail.appendChild(imgEl);
                thumbnailContainer.appendChild(thumbnail);
            });

            // Ensure thumbnails are clickable
            thumbnailContainer.addEventListener('click', (e) => {
                const thumbnail = e.target.closest('.thumbnail');
                if (thumbnail) {
                    const index = parseInt(thumbnail.dataset.index);
                    this.setActiveImage(index);
                }
            });
        }
    }



    // Navigate images (prev/next)
    navigateImages(direction) {
        if (direction === 'prev') {
            this.currentImageIndex = (this.currentImageIndex - 1 + this.productImages.length) % this.productImages.length;
        } else {
            this.currentImageIndex = (this.currentImageIndex + 1) % this.productImages.length;
        }

        this.setActiveImage(this.currentImageIndex);
    }

    // Set active image
    setActiveImage(index) {
        this.currentImageIndex = index;

        // Update main image
        const mainImageEl = this.overlay.querySelector('.main-image');
        if (mainImageEl) {
            mainImageEl.src = this.productImages[index];
        }

        // Update active thumbnail: Remove active class from all thumbnails
        const thumbnails = this.overlay.querySelectorAll('.thumbnail');
        thumbnails.forEach((thumb, idx) => {
            if (idx === index) {
                thumb.classList.add('active');
            } else {
                thumb.classList.remove('active');
            }
        });
    }

    // Switch tabs
    switchTab(tabId) {
        // Update tab buttons
        this.overlay.querySelectorAll('.tab-button').forEach(btn => {
            if (btn.dataset.tab === tabId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update tab panels
        this.overlay.querySelectorAll('.tab-panel').forEach(panel => {
            if (panel.id === `${tabId}-panel`) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
    }

    // Add to cart from overlay
    addToCartFromOverlay(quantity) {
        if (!this.currentProduct || !this.cart) return;

        // Create a temporary product card object with the same structure
        // as expected by the existing addToCart method
        const tempProductCard = {
            dataset: {
                productId: this.currentProductId
            },
            querySelector: (selector) => {
                switch (selector) {
                    case 'h3':
                        return { textContent: this.currentProduct.name };
                    case '.category':
                        return { textContent: this.currentProduct.category };
                    case '.price':
                    case '.current-price':
                        return { textContent: this.currentProduct.currentPrice };
                    case 'img':
                        return { src: this.productImages[0] };
                    case '.qty-display':
                        return { textContent: quantity.toString() };
                    case '.add-to-cart':
                        return {
                            innerHTML: '<i class="fas fa-cart-plus"></i> Add to Cart',
                            disabled: false
                        };
                    default:
                        return null;
                }
            }
        };

        // Use the existing cart functionality
        this.cart.addToCart(tempProductCard);

        // Close the overlay after adding to cart
        this.closeOverlay();
    }

    // Close overlay
    closeOverlay() {
        this.overlay.style.display = 'none';
        document.body.style.overflow = 'auto'; // Re-enable scrolling
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const cart = new ShoppingCart();
    const productListing = new ProductListing(cart);
    // const productFilter = new ProductFilter();
    const productOverlay = new ProductOverlay(cart);

    // Reset quantities
    productListing.resetQuantities();

    // Initial cart count update
    cart.updateCartCount();

    // Load products for filtering

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
        
        /* Product Overlay Animations */
        .product-overlay {
            animation: fadeIn 0.3s ease-out;
        }
        
        .product-overlay-content {
            animation: slideIn 0.4s ease-out;
        }
        
        @keyframes slideIn {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        /* Thumbnail styles */
        .thumbnail {
            cursor: pointer;
            opacity: 0.7;
            transition: all 0.2s ease;
            border: 2px solid transparent;
        }
        
        .thumbnail:hover {
            opacity: 0.9;
        }
        
        .thumbnail.active {
            opacity: 1;
            border-color: #4a90e2;
        }
        
        /* Tab transition */
        .tab-panel {
            display: none;
            animation: fadeIn 0.3s;
        }
        
        .tab-panel.active {
            display: block;
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