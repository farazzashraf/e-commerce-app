document.addEventListener("DOMContentLoaded", function () {
    const searchToggle = document.getElementById('searchToggle');
    const searchBar = document.getElementById('searchBar');
    const closeSearch = document.getElementById('closeSearch');
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarClose = document.getElementById('sidebarClose');
    const overlay = document.getElementById('overlay');
    const cartCount = document.querySelector('.cart-count');  // Cart count element
    const searchInput = document.getElementById('searchInput');  // Declare the search input element
    const searchResults = document.getElementById("searchResults");
    const authLinks = document.querySelectorAll('.auth-links-mobile a'); // Select all auth links
    const productList = document.getElementById("productList");

    // Search functionality
    searchToggle.addEventListener('click', () => {
        searchBar.classList.add('active');
        searchInput.focus();
    });

    closeSearch.addEventListener('click', (e) => {
        e.stopPropagation();
        searchBar.classList.remove('active');
    });

    // Sidebar functionality
    menuToggle.addEventListener('click', () => {
        sidebar.classList.add('active');
        overlay.classList.add('active');
    });

    function closeSidebar() {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    }

    sidebarClose.addEventListener('click', closeSidebar);
    overlay.addEventListener('click', closeSidebar);

    sidebarClose.addEventListener('click', closeSidebar);
    overlay.addEventListener('click', closeSidebar);

    // Close sidebar when clicking login/logout/signup links
    authLinks.forEach(link => {
        link.addEventListener('click', closeSidebar);
    });

    // Close search bar when pressing Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchBar.classList.remove('active');
            closeSidebar();
        }
    });

    // Close search bar when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-bar') && !e.target.closest('.search-icon')) {
            searchBar.classList.remove('active');
        }
    });

    // searchInput.addEventListener("keypress", function (event) {
    //     if (event.key === "Enter") {
    //         let query = searchInput.value.trim();
    //         if (query) {
    //             // Redirect to home page with the search query as a URL parameter
    //             window.location.href = `{% url 'home' %}?q=${encodeURIComponent(query)}`;
    //         }
    //     }
    // });

    // 🔹 **Fetch All Products (Reusable)**
    function fetchAllProducts() {
        fetch(`/products/`)
            .then((response) => response.json())
            .then((data) => {
                productList.innerHTML = "";
                data.products.forEach((product) => {
                    const imageUrl = product.image_url || "/static/images/default-product.jpg";
                    const item = document.createElement("div");
                    item.classList.add("product-item");
                    item.innerHTML = `
                        <a href="/product/${product.id}" class="product-link">
                            <img src="${imageUrl}" alt="${product.name}" class="product-image">
                            <h3>${product.name}</h3>
                            <p>₹${product.price}</p>
                        </a>
                    `;
                    productList.appendChild(item);
                });
            })
            .catch((error) => console.error("Error loading products:", error));
    }


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
                    const cartCount = data.cart_count || 0;  // Default to 0 if undefined
                    cartCountElement.textContent = cartCount; // Set the count

                    // Show or hide the cart count element based on the count
                    if (cartCount > 0) {
                        cartCountElement.style.display = 'block'; // Show the count
                    } else {
                        cartCountElement.style.display = 'none'; // Hide the count
                    }
                }
            })
            .catch(error => console.error('Error updating cart count:', error));
    }

    // Listen for the 'cart-updated' event to update the cart count
    document.addEventListener('cart-updated', updateCartCount);

    // Initialize the cart count on page load
    updateCartCount();

    // Update cart count when the page is loaded (e.g., after clicking back button)
    window.onload = function () {
        updateCartCount();
    };

    // Also update cart count when the tab becomes visible again (e.g., after switching tabs)
    document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === 'visible') {
            updateCartCount();
        }
    });

    // Category dropdown toggle
    const categoryToggle = document.getElementById('categoryToggle');
    const categoryDropdown = document.getElementById('categoryDropdown');

    categoryToggle.addEventListener('click', () => {
        categoryDropdown.classList.toggle('open');
        categoryToggle.classList.toggle('open');
    });

    // Account dropdown toggle
    const accountToggle = document.getElementById('accountToggle');
    const accountDropdown = document.getElementById('accountDropdown');

    accountToggle.addEventListener('click', () => {
        accountDropdown.classList.toggle('open');
        accountToggle.classList.toggle('open');
    });

    // Category item selection
    const categoryItems = document.querySelectorAll('.category-item');

    categoryItems.forEach(item => {
        item.addEventListener('click', () => {
            // Remove active class from all items
            categoryItems.forEach(i => i.classList.remove('active'));
            // Add active class to clicked item
            item.classList.add('active');
        });
    });

    // Update cart count from existing count if available
    const cartCountElement = document.getElementById('cartCount');
    const headerCartCount = document.querySelector('.cart-count');

    if (headerCartCount && cartCountElement) {
        cartCountElement.textContent = headerCartCount.textContent;
    }

});

// Add this JavaScript to enhance the dropdown functionality
document.addEventListener('DOMContentLoaded', function() {
    // For accessibility - allow keyboard navigation
    const profileToggle = document.querySelector('.profile-toggle');
    const dropdownMenu = document.querySelector('.dropdown-menu');
    
    if (profileToggle) {
        // Add keyboard support
        profileToggle.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                dropdownMenu.classList.toggle('show');
                
                if (dropdownMenu.classList.contains('show')) {
                    // Focus the first item in the dropdown
                    const firstItem = dropdownMenu.querySelector('.dropdown-item');
                    if (firstItem) firstItem.focus();
                }
            }
        });
        
        // Add tabindex for keyboard focus
        profileToggle.setAttribute('tabindex', '0');
        profileToggle.setAttribute('role', 'button');
        profileToggle.setAttribute('aria-haspopup', 'true');
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.user-profile-dropdown')) {
                dropdownMenu.classList.remove('show');
            }
        });
    }
    
    // Add appropriate ARIA attributes to dropdown items
    const dropdownItems = document.querySelectorAll('.dropdown-item');
    dropdownItems.forEach(item => {
        item.setAttribute('role', 'menuitem');
    });
});

