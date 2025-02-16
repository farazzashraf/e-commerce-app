document.addEventListener("DOMContentLoaded", function () {
    const searchToggle = document.getElementById('searchToggle');
    const searchBar = document.getElementById('searchBar');
    const closeSearch = document.getElementById('closeSearch');
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarClose = document.getElementById('sidebarClose');
    const overlay = document.getElementById('overlay');
    const cartCount = document.querySelector('.cart-count');  // Cart count element

    // Search functionality
    searchToggle.addEventListener('click', () => {
        searchBar.classList.add('active');
        searchBar.querySelector('input').focus();
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

    // Search functionality on input
    searchInput.addEventListener('input', function () {
        searchProducts();
    });

    // Function to update the cart count from localStorage
    function updateCartCount() {
        const cart = JSON.parse(localStorage.getItem('cart')) || {};
        const cartCountValue = Object.values(cart).reduce((acc, product) => acc + product.quantity, 0);
        if (cartCountValue === 0) {
            cartCount.style.display = 'none'; // Hide cart count if zero
        } else {
            cartCount.style.display = 'inline'; // Show cart count
            cartCount.textContent = cartCountValue; // Update cart count text
        }
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

});



