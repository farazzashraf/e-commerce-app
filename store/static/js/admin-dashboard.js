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