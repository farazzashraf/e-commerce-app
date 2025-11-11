// Mobile Menu Toggle
const mobileMenuBtn = document.getElementById('mobileMenuBtn')
const closeMobileMenuBtn = document.getElementById('closeMobileMenuBtn')
const mobileMenu = document.querySelector('.mobile-menu')

// Change from classList.add/remove('open') to translate classes
if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', function () {
        mobileMenu.classList.remove('-translate-x-full');
    });
}

if (closeMobileMenuBtn) {
    closeMobileMenuBtn.addEventListener('click', function () {
        mobileMenu.classList.add('-translate-x-full');
    });
}


// Modal Functions
function openModal(product) {
    document.getElementById('modalProductName').textContent = product.name;

    // Calculate discount percentage if original_price is available and greater than price
    let priceHtml = `₹${product.price}`;
    if (product.original_price && parseFloat(product.original_price) > parseFloat(product.price)) {
        const discountPercentage = Math.round(
            ((parseFloat(product.original_price) - parseFloat(product.price)) / parseFloat(product.original_price)) * 100
        );
        priceHtml = `<span class="line-through text-gray-400">₹${product.original_price}</span> 
                     <span class="ml-2">₹${product.price}</span> 
                     <span class="ml-2 text-green-400">(${discountPercentage}% off)</span>`;
    }
    document.getElementById('modalProductPrice').innerHTML = priceHtml;

    document.getElementById('modalProductStock').textContent = product.stock;
    document.getElementById('modalProductStatus').textContent = product.is_active ? 'Active' : 'Inactive';

    const variantsList = document.getElementById('modalProductVariants');
    variantsList.innerHTML = product.variants.length > 0
        ? product.variants.map(v => `<li>${v.color}, ${v.size}, ₹${v.price}</li>`).join('')
        : '<li class="text-gray-400">No variants available</li>';

    document.getElementById('productModal').classList.remove('hidden');
}


function closeModal() {
    document.getElementById('productModal').classList.add('hidden');
}

// Add click event listeners to product rows (Desktop)
document.querySelectorAll('tr.hover\\:bg-navy').forEach(row => {
    row.addEventListener('click', () => {
        const cells = row.querySelectorAll('td');
        const product = {
            name: cells[0].querySelector('.font-medium').textContent,
            price: cells[1].textContent.replace('₹', '').trim(),
            original_price: row.getAttribute('data-original-price').replace('₹', '').trim(),
            stock: cells[2].textContent.trim().split(' ')[0],
            is_active: cells[3].querySelector('span').textContent.trim() === 'Active',
            variants: Array.from(row.querySelectorAll('td:nth-child(1) .variant-details li')).map(li => {
                const [color, size, price] = li.textContent.split(', ');
                return { color, size, price: price.replace('₹', '').trim() };
            })
        };

        openModal(product);
    });
});

// Mobile: Add click event listeners to product cards
document.querySelectorAll('.md\\:hidden .bg-navy.rounded-lg').forEach(card => {
    card.addEventListener('click', () => {
        // Use selectors appropriate for your mobile card structure.
        const nameElem = card.querySelector('h3.font-medium');
        const priceElem = card.querySelector('p.text-sm');
        // Assume you store original price in a data attribute on the card.
        const originalPrice = card.getAttribute('data-original-price');
        // For stock, assume the card structure contains a block with stock info.
        const stockElem = card.querySelector('.mt-4 .flex.justify-between span:last-child');
        // For active status, check for the presence of a green icon.
        const statusElem = card.querySelector('span.text-green-400, span.text-red-400');
        // Optionally, assume variant details are stored in a hidden <ul class="variant-details">
        const variantListElem = card.querySelector('.variant-details');

        const name = nameElem ? nameElem.textContent : '';
        const price = priceElem ? priceElem.textContent.replace('₹', '').trim() : '';
        const origPrice = originalPrice ? originalPrice.replace('₹', '').trim() : price;
        const stock = stockElem ? stockElem.textContent.trim() : '';
        const is_active = statusElem ? statusElem.classList.contains('text-green-400') : false;
        let variants = [];
        if (variantListElem) {
            variants = Array.from(variantListElem.querySelectorAll('li')).map(li => {
                const parts = li.textContent.split(', ');
                return { color: parts[0], size: parts[1], price: parts[2].replace('₹', '').trim() };
            });
        }
        const product = {
            name,
            price,
            original_price: origPrice,
            stock,
            is_active,
            variants
        };
        openModal(product);
    });
});

// Close modal when clicking outside
document.getElementById('productModal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('productModal')) {
        closeModal();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.action-button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();  // Prevent click from triggering the modal open
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    // Elements
    const searchInput = document.getElementById('search-input');
    const statusFilter = document.getElementById('status-filter');
    const stockFilter = document.getElementById('stock-filter');
    const variantsFilter = document.getElementById('variants-filter');
    const sortBy = document.getElementById('sort-by');
    const minPrice = document.getElementById('min-price');
    const maxPrice = document.getElementById('max-price');
    const advancedFiltersBtn = document.getElementById('advanced-filters-btn');
    const advancedFilters = document.getElementById('advanced-filters');
    const applyFiltersBtn = document.getElementById('apply-filters');
    const resetFiltersBtn = document.getElementById('reset-filters');
    const clearSearchBtn = document.getElementById('clear-search');
    const noResults = document.getElementById('no-results');
    const productCount = document.getElementById('product-count');

    // All product elements (for desktop and mobile)
    const productRows = document.querySelectorAll('.product-row');
    const productCards = document.querySelectorAll('.product-card');

    // Toggle advanced filters
    advancedFiltersBtn.addEventListener('click', function () {
        advancedFilters.classList.toggle('hidden');
        // Change icon based on state
        const icon = this.querySelector('i');
        if (advancedFilters.classList.contains('hidden')) {
            icon.classList.remove('fa-times');
            icon.classList.add('fa-sliders-h');
        } else {
            icon.classList.remove('fa-sliders-h');
            icon.classList.add('fa-times');
        }
    });

    // Filter products function
    function filterProducts() {
        const searchValue = searchInput.value.toLowerCase();
        const statusValue = statusFilter.value;
        const stockValue = stockFilter.value;
        const variantsValue = variantsFilter?.value || '';
        const minPriceValue = minPrice?.value ? parseFloat(minPrice.value) : 0;
        const maxPriceValue = maxPrice?.value ? parseFloat(maxPrice.value) : Infinity;

        let visibleCount = 0;

        // Filter desktop rows
        productRows.forEach(row => {
            const name = row.dataset.name;
            const status = row.dataset.status;
            const stock = parseInt(row.dataset.stock);
            const price = parseFloat(row.dataset.price);
            const hasVariants = row.dataset.variants === 'true';

            let visible = name.includes(searchValue);

            // Status filter
            if (statusValue && status !== statusValue) {
                visible = false;
            }

            // Stock filter
            if (stockValue) {
                if (stockValue === 'in-stock' && stock <= 0) visible = false;
                if (stockValue === 'low-stock' && (stock > 10 || stock <= 0)) visible = false;
                if (stockValue === 'out-of-stock' && stock > 0) visible = false;
            }

            // Variants filter
            if (variantsValue) {
                if (variantsValue === 'with-variants' && !hasVariants) visible = false;
                if (variantsValue === 'no-variants' && hasVariants) visible = false;
            }

            // Price range filter
            if (price < minPriceValue || price > maxPriceValue) {
                visible = false;
            }

            row.classList.toggle('hidden', !visible);
            if (visible) visibleCount++;
        });

        // Filter mobile cards
        productCards.forEach(card => {
            const name = card.dataset.name;
            const status = card.dataset.status;
            const stock = parseInt(card.dataset.stock);
            const price = parseFloat(card.dataset.price);
            const hasVariants = card.dataset.variants === 'true';

            let visible = name.includes(searchValue);

            // Status filter
            if (statusValue && status !== statusValue) {
                visible = false;
            }

            // Stock filter
            if (stockValue) {
                if (stockValue === 'in-stock' && stock <= 0) visible = false;
                if (stockValue === 'low-stock' && (stock > 10 || stock <= 0)) visible = false;
                if (stockValue === 'out-of-stock' && stock > 0) visible = false;
            }

            // Variants filter
            if (variantsValue) {
                if (variantsValue === 'with-variants' && !hasVariants) visible = false;
                if (variantsValue === 'no-variants' && hasVariants) visible = false;
            }

            // Price range filter
            if (price < minPriceValue || price > maxPriceValue) {
                visible = false;
            }

            card.classList.toggle('hidden', !visible);
        });

        // Update product count
        productCount.textContent = visibleCount;

        // Show/hide no results message
        noResults.classList.toggle('hidden', visibleCount > 0);

        return visibleCount;
    }

    // Sort products function
    function sortProducts() {
        const sortValue = sortBy.value;
        const tableBody = document.getElementById('products-table-body');
        const mobileContainer = document.getElementById('products-mobile-container');

        // Convert NodeLists to arrays for sorting
        const rowsArray = Array.from(productRows);
        const cardsArray = Array.from(productCards);

        // Sort based on selected option
        switch (sortValue) {
            case 'name-asc':
                rowsArray.sort((a, b) => a.dataset.name.localeCompare(b.dataset.name));
                cardsArray.sort((a, b) => a.dataset.name.localeCompare(b.dataset.name));
                break;
            case 'name-desc':
                rowsArray.sort((a, b) => b.dataset.name.localeCompare(a.dataset.name));
                cardsArray.sort((a, b) => b.dataset.name.localeCompare(a.dataset.name));
                break;
            case 'price-asc':
                rowsArray.sort((a, b) => parseFloat(a.dataset.price) - parseFloat(b.dataset.price));
                cardsArray.sort((a, b) => parseFloat(a.dataset.price) - parseFloat(b.dataset.price));
                break;
            case 'price-desc':
                rowsArray.sort((a, b) => parseFloat(b.dataset.price) - parseFloat(a.dataset.price));
                cardsArray.sort((a, b) => parseFloat(b.dataset.price) - parseFloat(a.dataset.price));
                break;
            case 'stock-asc':
                rowsArray.sort((a, b) => parseInt(a.dataset.stock) - parseInt(b.dataset.stock));
                cardsArray.sort((a, b) => parseInt(a.dataset.stock) - parseInt(b.dataset.stock));
                break;
            case 'stock-desc':
                rowsArray.sort((a, b) => parseInt(b.dataset.stock) - parseInt(a.dataset.stock));
                cardsArray.sort((a, b) => parseInt(b.dataset.stock) - parseInt(a.dataset.stock));
                break;
        }

        // Reorder DOM elements
        rowsArray.forEach(row => tableBody.appendChild(row));
        cardsArray.forEach(card => mobileContainer.appendChild(card));
    }

    // Reset all filters
    function resetFilters() {
        searchInput.value = '';
        statusFilter.value = '';
        stockFilter.value = '';
        if (variantsFilter) variantsFilter.value = '';
        if (minPrice) minPrice.value = '';
        if (maxPrice) maxPrice.value = '';
        sortBy.value = 'name-asc';

        // Hide advanced filters
        advancedFilters.classList.add('hidden');
        const icon = advancedFiltersBtn.querySelector('i');
        icon.classList.remove('fa-times');
        icon.classList.add('fa-sliders-h');

        // Reset filtering
        productRows.forEach(row => row.classList.remove('hidden'));
        productCards.forEach(card => card.classList.remove('hidden'));
        noResults.classList.add('hidden');

        // Update count
        productCount.textContent = productRows.length;

        // Sort by default
        sortProducts();
    }

    // Event listeners
    searchInput.addEventListener('input', filterProducts);
    statusFilter.addEventListener('change', filterProducts);
    stockFilter.addEventListener('change', filterProducts);
    sortBy.addEventListener('change', sortProducts);

    if (variantsFilter) variantsFilter.addEventListener('change', filterProducts);
    if (minPrice) minPrice.addEventListener('input', filterProducts);
    if (maxPrice) maxPrice.addEventListener('input', filterProducts);

    applyFiltersBtn.addEventListener('click', filterProducts);
    resetFiltersBtn.addEventListener('click', resetFilters);
    clearSearchBtn.addEventListener('click', resetFilters);

    // Initialize with default sort
    sortProducts();
});

document.addEventListener('DOMContentLoaded', function() {
    // Activate messages with animation
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Trigger initial animation
        setTimeout(() => {
            alert.classList.add('active');
        }, 50);
        
        // Auto-dismiss after 3 seconds
        const dismissTimer = setTimeout(() => {
            dismissAlert(alert);
        }, 3000);

        // Manual close
        alert.querySelector('.close-alert').addEventListener('click', () => {
            clearTimeout(dismissTimer);
            dismissAlert(alert);
        });
    });

    function dismissAlert(alert) {
        alert.classList.remove('active');
        alert.classList.add('exit');
        
        // Remove element after animation
        setTimeout(() => {
            alert.remove();
        }, 400); // Match transition duration
    }
});