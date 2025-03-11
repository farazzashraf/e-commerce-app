function clearFilterForm() {
    var form = document.getElementById('filterForm');
    if (form) {
        // Clear text and number inputs
        form.querySelectorAll('input[type="text"], input[type="number"]').forEach(function (el) {
            el.value = '';
        });
        // Reset selects to default (first option)
        form.querySelectorAll('select').forEach(function (el) {
            el.selectedIndex = 0;
        });
    }
}

// Function to determine if there are active filters
function hasActiveFilters() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.has('category') ||
        urlParams.has('min_price') ||
        urlParams.has('max_price') ||
        urlParams.has('status') ||
        urlParams.has('stock_status') ||
        urlParams.has('sort_by') ||
        (urlParams.has('q') && urlParams.get('q') !== '');
}

// Function to remove a specific filter and resubmit the form
function removeFilter(filterName) {
    const urlParams = new URLSearchParams(window.location.search);

    if (filterName === 'price') {
        urlParams.delete('min_price');
        urlParams.delete('max_price');
    } else {
        urlParams.delete(filterName);
    }

    window.location.href = window.location.pathname + '?' + urlParams.toString();
}

// Function to clear all filters
function clearAllFilters() {
    window.location.href = window.location.pathname;
}

// Function to clear filter form without submitting
function clearFilterForm() {
    const form = document.getElementById('filterForm');
    form.reset();

    // Clear select elements that might not be reset by form.reset()
    document.getElementById('category').value = '';
    document.getElementById('status').value = '';
    document.getElementById('stock_status').value = '';
    document.getElementById('sort_by').value = 'id_asc'; // Reset to default

    // Clear number inputs
    document.getElementsByName('min_price')[0].value = '';
    document.getElementsByName('max_price')[0].value = '';
}

// Show or hide the filter status bar based on whether filters are applied
document.addEventListener('DOMContentLoaded', function () {
    const filterStatusBar = document.getElementById('filterStatusBar');
    if (filterStatusBar) {
        filterStatusBar.style.display = hasActiveFilters() ? 'flex' : 'none';
    }
});

function showPromoModal() {
    document.getElementById('promoModal').classList.remove('hidden');
    // Set default dates
    const today = new Date();
    const nextMonth = new Date();
    nextMonth.setMonth(today.getMonth() + 1);

    document.getElementById('validFrom').valueAsDate = today;
    document.getElementById('validUntil').valueAsDate = nextMonth;
}

function closePromoModal() {
    document.getElementById('promoModal').classList.add('hidden');
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('promoModal');
    if (event.target == modal) {
        closePromoModal();
    }
}