document.addEventListener('DOMContentLoaded', function () {
    // Status filter functionality
    const statusFilter = document.getElementById('statusFilter');

    statusFilter.addEventListener('change', function () {
        const selectedStatus = this.value;
        filterOrders(selectedStatus);
    });

    // Function to filter orders based on status
    function filterOrders(status) {
        // Get all order items (both desktop and mobile views)
        const desktopOrderRows = document.querySelectorAll('.desktop-table tbody tr');
        const mobileOrderItems = document.querySelectorAll('.mobile-order-list .order-item');

        // Show loading indication
        document.querySelectorAll('.skeleton').forEach(skeleton => {
            skeleton.classList.remove('d-none');
        });

        // Apply filter after small delay to show loading effect
        setTimeout(() => {
            // Desktop view filtering
            desktopOrderRows.forEach(row => {
                const orderStatus = row.querySelector('td:nth-child(4) .badge').textContent.toLowerCase();

                if (status === 'all' || orderStatus === status.toLowerCase()) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });

            // Mobile view filtering
            mobileOrderItems.forEach(item => {
                const orderStatus = item.querySelector('.order-status-price .badge').textContent.toLowerCase();

                if (status === 'all' || orderStatus === status.toLowerCase()) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });

            // Update order count in the header
            updateOrderCount();

            // Hide loading skeletons
            document.querySelectorAll('.skeleton').forEach(skeleton => {
                skeleton.classList.add('d-none');
            });
        }, 300);
    }

    function updateOrderCount() {
        const desktopVisible = document.querySelectorAll('.desktop-table tbody tr:not([style*="display: none"])').length;
        const totalOrdersBadge = document.querySelector('.card-header .badge');
        if (totalOrdersBadge) {
            totalOrdersBadge.textContent = `${desktopVisible} ${desktopVisible === 1 ? 'Order' : 'Orders'}`;
        }
    }

    // Search implementation
    const searchInput = document.querySelector('.search-input');

    searchInput.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase().trim();
        searchOrders(searchTerm);
        updateOrderCount(); // update order count after search
    });

    function searchOrders(term) {
        term = term.toLowerCase();
        const desktopOrderRows = document.querySelectorAll('.desktop-table tbody tr');
        const mobileOrderItems = document.querySelectorAll('.mobile-order-list .order-item');

        document.querySelectorAll('.skeleton').forEach(skeleton => skeleton.classList.remove('d-none'));

        setTimeout(() => {
            if (term === '') {
                // If search is cleared, show all orders
                desktopOrderRows.forEach(row => row.style.display = '');
                mobileOrderItems.forEach(item => item.style.display = '');
            } else {
                // Desktop search filtering
                desktopOrderRows.forEach(row => {
                    const orderIdText = row.querySelector('td:nth-child(1)').textContent.toLowerCase();
                    const customerName = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
                    const totalPriceText = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
                    const statusText = row.querySelector('td:nth-child(4)').textContent.toLowerCase();
                    const actionsText = row.querySelector('td:nth-child(5)').textContent.toLowerCase();

                    if (
                        orderIdText.includes(term) ||
                        customerName.includes(term) ||
                        totalPriceText.includes(term) ||
                        statusText.includes(term) ||
                        actionsText.includes(term)
                    ) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });

                // Mobile search filtering
                mobileOrderItems.forEach(item => {
                    const orderIdText = item.querySelector('.order-id')?.textContent.toLowerCase();
                    const customerName = item.querySelector('.customer-name')?.textContent.toLowerCase();
                    const totalPriceText = item.querySelector('.order-price')?.textContent.toLowerCase();
                    const statusText = item.querySelector('.order-status-price .badge')?.textContent.toLowerCase();
                    const actionsText = item.querySelector('.order-actions')?.textContent.toLowerCase();

                    if (
                        orderIdText.includes(term) ||
                        customerName.includes(term) ||
                        totalPriceText.includes(term) ||
                        statusText.includes(term) ||
                        actionsText.includes(term)
                    ) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            }

            updateOrderCount();
            document.querySelectorAll('.skeleton').forEach(skeleton => skeleton.classList.add('d-none'));
        }, 300);
    }



    // Combine search with status filter
    const searchButton = document.querySelector('.input-group .btn');

    searchButton.addEventListener('click', function () {
        const searchTerm = document.querySelector('.search-input').value.toLowerCase().trim();
        searchOrders(searchTerm);
        updateOrderCount()
    });


    // Add event listener for refresh button in empty state
    const refreshButton = document.querySelector('.text-center .btn-primary');
    if (refreshButton) {
        refreshButton.addEventListener('click', function () {
            location.reload();
        });
    }

    // Pull-to-refresh functionality (from your existing code)
    let startY = 0;
    let indicator = document.getElementById('refreshIndicator');

    document.addEventListener('touchstart', function (e) {
        startY = e.touches[0].clientY;
    }, { passive: true });

    document.addEventListener('touchmove', function (e) {
        const currentY = e.touches[0].clientY;
        const scrollTop = document.documentElement.scrollTop;

        // Only trigger pull-to-refresh when at the top of the page
        if (scrollTop === 0 && currentY > startY) {
            const pullDistance = Math.min((currentY - startY) / 100, 1);
            indicator.style.transform = `scaleX(${pullDistance})`;

            if (pullDistance === 1) {
                // Visual feedback when fully pulled
                indicator.style.height = '4px';
            }
        }
    }, { passive: true });

    document.addEventListener('touchend', function (e) {
        const currentY = e.changedTouches[0].clientY;
        const scrollTop = document.documentElement.scrollTop;

        if (scrollTop === 0 && (currentY - startY) > 100) {
            // Trigger refresh animation
            indicator.style.transform = 'scaleX(1)';
            setTimeout(() => {
                // Reset indicator after "refresh"
                indicator.style.transform = 'scaleX(0)';
                indicator.style.height = '3px';

                // Show loading skeletons
                document.querySelectorAll('.skeleton').forEach(skeleton => {
                    skeleton.classList.remove('d-none');
                });

                // After "loading", reload the page
                setTimeout(() => {
                    location.reload();
                }, 1500);
            }, 1000);
        } else {
            // Reset without refreshing
            indicator.style.transform = 'scaleX(0)';
            indicator.style.height = '3px';
        }
    }, { passive: true });

    // Add click listeners to desktop order rows
    document.querySelectorAll('.desktop-table tbody tr.order-row').forEach(function (row) {
        row.addEventListener('click', function () {
            const orderId = this.getAttribute('data-order-id');
            loadOrderDetails(orderId);
        });
    });

    document.querySelectorAll('.mobile-order-list .order-item').forEach(function (item) {
        item.addEventListener('click', function () {
            const orderId = this.getAttribute('data-order-id');
            console.log("Clicked Order ID:", orderId); // Debugging
            loadOrderDetails(orderId);
        });

        item.addEventListener('touchstart', function () { // Fix for mobile
            const orderId = this.getAttribute('data-order-id');
            console.log("Touched Order ID:", orderId); // Debugging
            loadOrderDetails(orderId);
        });
    });


    updateOrderCount();
});

function loadOrderDetails(orderId) {
    const modalContent = document.getElementById('order-details-content');
    const summaryContent = document.getElementById('order-summary');
    modalContent.innerHTML = '<p>Loading order details...</p>';
    summaryContent.innerHTML = '';

    fetch('/store-admin/order-details/' + orderId + '/')
        .then(response => response.json())
        .then(data => {
            // Build HTML for order items table
            let itemsHtml = '<h6>Order #' + orderId + '</h6>';
            itemsHtml += '<table class="table table-bordered">';
            itemsHtml += '<thead><tr><th>Product ID</th><th>Product Name</th><th>Quantity</th><th>Unit Price</th></tr></thead>';
            itemsHtml += '<tbody>';
            data.items.forEach(function (item) {
                itemsHtml += '<tr>';
                itemsHtml += '<td>' + item.product_id + '</td>';
                itemsHtml += '<td>' + item.product_name + '</td>';
                itemsHtml += '<td>' + item.quantity + '</td>';
                itemsHtml += '<td>₹' + item.price + '</td>';
                itemsHtml += '</tr>';
            });
            itemsHtml += '</tbody></table>';
            modalContent.innerHTML = itemsHtml;

            // Calculate selling price if not provided by the backend (or override with calculated value)
            let sellingPrice = data.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);

            // Build HTML for price breakdown summary
            let summaryHtml = '<table class="table table-bordered">';
            summaryHtml += '<tbody>';
            summaryHtml += '<tr><th>Selling Price</th><td>₹' + sellingPrice.toFixed(2) + '</td></tr>';
            summaryHtml += '<tr><th>Discount</th><td>₹' + data.discount_rate + '</td></tr>';
            summaryHtml += '<tr><th>Shipping Rate</th><td>₹' + data.shipping_rate + '</td></tr>';
            summaryHtml += '<tr><th>Total Price</th><td>₹' + data.order_total + '</td></tr>';
            summaryHtml += '</tbody></table>';
            summaryContent.innerHTML = summaryHtml;

            // Show the modal using Bootstrap's Modal API
            var orderDetailsModal = new bootstrap.Modal(document.getElementById('orderDetailsModal'));
            orderDetailsModal.show();
        })
        .catch(error => {
            modalContent.innerHTML = '<p>Error loading order details.</p>';
            console.error('Error fetching order details:', error);
        });
}

