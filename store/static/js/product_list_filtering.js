// Product Sorting Functionality
class ProductSorter {
    constructor() {
        this.products = [];
        this.initEventListeners();
    }

    // Initialize event listeners
    initEventListeners() {
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
            const currentPriceEl = card.querySelector('.current-price') || card.querySelector('.price');
            let currentPrice = currentPriceEl ? parseFloat(currentPriceEl.textContent.replace('₹', '').trim()) : 0;
            let dateAdded = card.dataset.added ? new Date(card.dataset.added) : new Date();

            this.products.push({
                id: productId,
                element: card,
                name: name,
                price: currentPrice,
                dateAdded: dateAdded,
            });
        });
        this.sortProducts(document.getElementById('sort-options').value);
    }

    // Sort products
    sortProducts(sortOption) {
        switch (sortOption) {
            case 'price-low':
                this.products.sort((a, b) => a.price - b.price);
                break;
            case 'price-high':
                this.products.sort((a, b) => b.price - a.price);
                break;
            case 'newest':
                this.products.sort((a, b) => b.dateAdded - a.dateAdded);
                break;
            default:
                break;
        }
        this.updateProductDisplay();
    }

    // Update product display based on sorted products
    updateProductDisplay() {
        const productGrid = document.querySelector('.product-grid');
        this.products.forEach(product => {
            productGrid.appendChild(product.element);
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const productSorter = new ProductSorter();
    productSorter.loadProductsFromDOM();
});
