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
    const authLinks = document.querySelectorAll('.auth-links-mobile a'); // Select all auth links

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

    // Search functionality on input
    searchInput.addEventListener('input', function () {
        searchProducts(); // Make sure to define the searchProducts function elsewhere
    });

    
    

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
});
