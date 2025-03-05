// Enhanced Product Filtering Functionality
class ProductFilter {
    constructor() {
        this.activeFilters = {
            category: 'All Items',
        };
        this.products = [];
        this.filteredProducts = [];
        this.initEventListeners();
    }

    // Initialize event listeners
    initEventListeners() {
        // Category filter buttons
        document.querySelectorAll('.filter-button').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const category = button.textContent.trim();
                this.setFilter('category', category);
                this.applyFilters();

                // Update active filter button
                document.querySelectorAll('.filter-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                button.classList.add('active');
            });
        });

        // Sort dropdown
        const sortDropdown = document.getElementById('sort-options');
        if (sortDropdown) {
            sortDropdown.addEventListener('change', () => {
                this.sortProducts(sortDropdown.value);
            });
        }
    }

    // Load all products from the DOM
    loadProductsFromDOM() {
        this.products = [];
        document.querySelectorAll('.product-card').forEach(card => {
            const productId = card.dataset.productId;
            const name = card.querySelector('h3').textContent;
            const category = card.querySelector('.category')?.textContent || 'Uncategorized';

            const originalPriceEl = card.querySelector('.original-price');
            const currentPriceEl = card.querySelector('.current-price') || card.querySelector('.price');

            let originalPrice = originalPriceEl ? parseFloat(originalPriceEl.textContent.replace('₹', '').trim()) : 0;
            let currentPrice = currentPriceEl ? parseFloat(currentPriceEl.textContent.replace('₹', '').trim()) : 0;

            // Get date added from the dataset attribute (assuming backend sets it)
            let dateAdded = card.dataset.added ? new Date(card.dataset.added) : new Date();

            this.products.push({
                id: productId,
                element: card,
                name: name,
                category: category,
                price: currentPrice,
                originalPrice: originalPrice,
                dateAdded: dateAdded,
            });
        });

        this.filteredProducts = [...this.products];  // Apply all products first
        this.sortProducts(document.getElementById('sort-options').value);  // Apply sorting
    }


    // Set a filter value
    setFilter(filterType, value) {
        this.activeFilters[filterType] = value;
        console.log(`Filter set: ${filterType} = ${value}`);
    }

    // Apply all active filters
    applyFilters() {
        this.showLoadingState();

        // Filter products
        this.filteredProducts = this.products.filter(product =>
            this.activeFilters.category === 'All Items' ||
            product.category.toLowerCase() === this.activeFilters.category.toLowerCase()
        );

        // Preserve last selected sorting option
        const sortDropdown = document.getElementById('sort-options');
        if (sortDropdown) {
            this.sortProducts(sortDropdown.value);
        } else {
            this.updateProductDisplay();  // Fallback if no sorting is selected
        }
    }

    sortProducts(sortOption) {
        this.showLoadingState();

        switch (sortOption) {
            case 'price-low':
                this.filteredProducts.sort((a, b) => a.price - b.price);
                break;

            case 'price-high':
                this.filteredProducts.sort((a, b) => b.price - a.price);
                break;

            case 'newest':
                this.filteredProducts.sort((a, b) => b.dateAdded - a.dateAdded);
                break;

            default: // 'featured' or reset sorting
                // Maintain filtered products, don't reset to all products
                break;
        }

        this.updateProductDisplay();
    }

    // Show loading state
    showLoadingState() {
        const productGrid = document.querySelector('.product-grid');
        const loader = document.querySelector('.loader');

        if (productGrid && loader) {
            productGrid.style.display = 'none';
            loader.style.display = 'block';
        }
    }

    // Hide loading state
    hideLoadingState() {
        const productGrid = document.querySelector('.product-grid');
        const loader = document.querySelector('.loader');

        if (productGrid && loader) {
            loader.style.display = 'none';
            productGrid.style.display = 'grid';
        }
    }

    // Update product display based on filtered products
    updateProductDisplay() {
        // Add a slight delay to simulate server processing
        setTimeout(() => {
            const productGrid = document.querySelector('.product-grid');

            // Hide all products first
            this.products.forEach(product => {
                product.element.style.display = 'none';
            });

            // Reorder products in the DOM based on filtered order
            this.filteredProducts.forEach(product => {
                productGrid.appendChild(product.element); // This moves elements to new positions
            });

            // Show filtered products
            this.filteredProducts.forEach(product => {
                product.element.style.display = 'flex';
            });

            // Add CSS for animations if not already present
            if (!document.getElementById('filter-animations')) {
                const style = document.createElement('style');
                style.id = 'filter-animations';
                style.textContent = `
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(10px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                    .product-card {
                        animation: fadeIn 0.4s ease;
                    }
                `;
                document.head.appendChild(style);
            }

            // Show "no products" message if needed
            if (this.filteredProducts.length === 0) {
                let noProductsMsg = document.querySelector('.no-products-message');

                if (!noProductsMsg) {
                    noProductsMsg = document.createElement('p');
                    noProductsMsg.className = 'no-products-message';
                    noProductsMsg.textContent = 'No products match your selected filters.';

                    const productGrid = document.querySelector('.product-grid');
                    if (!productGrid) {
                        console.error("Product grid element not found!");
                        return;
                    }

                    productGrid.parentNode.appendChild(noProductsMsg);
                }

                noProductsMsg.style.display = 'block';
            } else {
                const noProductsMsg = document.querySelector('.no-products-message');
                if (noProductsMsg) {
                    noProductsMsg.style.display = 'none';
                }
            }


            this.hideLoadingState();
        }, 500);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const productFilter = new ProductFilter();
    productFilter.loadProductsFromDOM();
});