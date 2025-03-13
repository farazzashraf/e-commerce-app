// Add this to your main JavaScript file or include it in a script tag
document.addEventListener('alpine:init', () => {
    Alpine.data('filterPanel', () => ({
        showFilters: false,

        init() {
            // Close filter panel when Escape key is pressed
            window.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.showFilters) {
                    this.showFilters = false;
                }
            });

            // Close filter panel when clicking outside
            this.$watch('showFilters', (value) => {
                if (value) {
                    document.body.classList.add('overflow-hidden'); // Prevent scrolling when filter is open
                } else {
                    document.body.classList.remove('overflow-hidden');
                }
            });

            // Handle query parameter changes
            this.updateActiveFilters();
        },

        updateActiveFilters() {
            // Optional: Automatically update the active filters based on URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.has('category') || urlParams.has('min_price') ||
                urlParams.has('max_price') || urlParams.has('status') ||
                urlParams.has('stock_status') ||
                (urlParams.has('sort_by') && urlParams.get('sort_by') !== 'id_asc')) {
                // There are active filters
                this.hasActiveFilters = true;
            } else {
                this.hasActiveFilters = false;
            }
        },

        clearAllFilters() {
            // Helper function to clear all filters at once
            const searchParam = new URLSearchParams(window.location.search).get('q');
            if (searchParam) {
                window.location.href = `${window.location.pathname}?q=${searchParam}`;
            } else {
                window.location.href = window.location.pathname;
            }
        }
    }));
});

// Show Images Modal
function showImagesModal(button) {
    const imageUrls = button.getAttribute("data-image-urls");

    if (!imageUrls) {
        console.error("No images found for this product.");
        return;
    }

    // Convert the comma-separated string into an array
    const images = imageUrls.split(",").map(url => url.trim());

    const modalContent = document.getElementById("imagesModalContent");
    modalContent.innerHTML = ""; // Clear previous images

    // Create image elements and append to modal
    images.forEach(url => {
        if (url) {
            const img = document.createElement("img");
            img.src = url;
            img.className = "w-32 h-32 object-cover m-2 rounded-lg border";
            modalContent.appendChild(img);
        }
    });

    // Show the modal
    document.getElementById("imagesModal").classList.remove("hidden");
}

// Close Images Modal
function closeImagesModal() {
    document.getElementById("imagesModal").classList.add("hidden");
}

// Show Stock Edit Modal
function showStockEditModal(productId) {
    const modal = document.getElementById("stockEditModal");

    if (!modal) {
        console.error("Stock Edit Modal not found!");
        return;
    }

    // Set the product ID in the hidden input field
    document.getElementById("productIdField").value = productId;

    // Show the modal
    modal.classList.remove("hidden");
    modal.classList.add("flex");
}

// Close Stock Edit Modal
function closeStockModal() {
    const modal = document.getElementById("stockEditModal");
    if (modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
    }
}

// Show Delete Modal
function showDeleteModal(productId, deleteUrl) {
    const modal = document.getElementById("deleteModal");

    if (!modal) {
        console.error("Delete Modal not found!");
        return;
    }

    // Set the form action dynamically
    document.getElementById("deleteForm").setAttribute("action", deleteUrl);

    // Show the modal
    modal.classList.remove("hidden");
    modal.classList.add("flex");
}

// Close Delete Modal
function closeDeleteModal() {
    const modal = document.getElementById("deleteModal");
    if (modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
    }
}
