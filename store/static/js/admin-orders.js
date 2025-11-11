document.addEventListener('DOMContentLoaded', function () {
    // Status filter functionality
    const statusFilter = document.getElementById('statusFilter');

    statusFilter.addEventListener('change', function () {
        const selectedStatus = this.value;
        console.log("Filter changed to:", selectedStatus);
        filterOrders(selectedStatus);
    });

    // Function to filter orders based on status
    function filterOrders(status) {
        // Get all order items (both desktop and mobile views)
        const desktopOrderRows = document.querySelectorAll('table.w-full tbody tr');
        const mobileOrderItems = document.querySelectorAll('.md\\:hidden .order-item');

        // Show loading indication
        document.querySelectorAll('.skeleton').forEach(skeleton => {
            skeleton.classList.remove('d-none');
        });

        // Apply filter after a small delay to show loading effect
        setTimeout(() => {
            // Desktop view filtering
            desktopOrderRows.forEach(row => {
                const badge = row.querySelector('td:nth-child(4) span');
                if (!badge) {
                    console.warn("No badge found for row:", row);
                    return;
                }
                const orderStatus = badge ? badge.textContent.trim().toLowerCase() : '';
                console.log("Desktop row order status:", orderStatus);

                if (status === 'all' || orderStatus === status.toLowerCase()) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });

            // Corrected mobile filtering code
            mobileOrderItems.forEach(item => {
                // Directly target the status badge using its common class pattern
                const statusBadge = item.querySelector('.status-badge');

                if (!statusBadge) {
                    console.warn("No status badge found for mobile item:", item);
                    return;
                }

                const statusText = statusBadge.textContent.trim().toLowerCase();
                const filterValue = status.toLowerCase();

                // Handle status mapping differences between backend and display
                const statusMap = {
                    'pending': 'pending',
                    'confirmed': 'confirmed',
                    'rejected': 'rejected',
                    'shipped': 'shipped',
                    'canceled': 'canceled'
                };

                const normalizedStatus = Object.keys(statusMap).find(key =>
                    statusText.includes(statusMap[key])
                ) || '';

                item.style.display = (status === 'all' || normalizedStatus === filterValue)
                    ? 'block'
                    : 'none';
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
        const desktopVisible = document.querySelectorAll(
            '.desktop-table tbody tr:not(.empty-row):not([style*="display: none"])'
        ).length;
        const totalOrdersBadge = document.querySelector('.card-header .badge');
        if (totalOrdersBadge) {
            totalOrdersBadge.textContent = `${desktopVisible} ${desktopVisible === 1 ? 'Order' : 'Orders'}`;
        }
    }

    // Search implementation
    const searchInput = document.querySelector('.search-input');
    const searchBtn = document.querySelector('.search-btn');

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            searchOrders(this.value.toLowerCase().trim());
        });
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', function () {
            searchOrders(searchInput.value.toLowerCase().trim());
        });
    }

    let searchTimeout;
    searchInput.addEventListener('input', function () {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchOrders(this.value.toLowerCase().trim());
        }, 300);
    });

    function searchOrders(term) {
        document.querySelectorAll('.order-item, table.w-full tr').forEach(el => {
            el.style.opacity = '0.5';
            el.style.transition = 'opacity 0.2s';
        });
        const desktopOrderRows = document.querySelectorAll('table.w-full tbody tr');
        const mobileOrderItems = document.querySelectorAll('.md\\:hidden .order-item');

        desktopOrderRows.forEach(row => {
            const orderId = row.querySelector('td:nth-child(1)').textContent.toLowerCase();
            const customerName = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
            const statusBadge = row.querySelector('td:nth-child(4) span');
            const statusText = statusBadge ? statusBadge.textContent.toLowerCase() : '';
            const rowText = orderId + customerName + statusText;

            row.style.display = rowText.includes(term) ? '' : 'none';
        });

        mobileOrderItems.forEach(item => {
            // Use the specific classes we added to mobile items
            const orderId = item.querySelector('.order-id').textContent.toLowerCase().replace('#', '');
            const customerName = item.querySelector('.customer-name').textContent.toLowerCase();
            const statusBadge = item.querySelector('[class*="bg-"]'); // Directly target the status badge
            const statusText = statusBadge ? statusBadge.textContent.toLowerCase() : '';

            // Combine all searchable fields
            const searchContent = `${orderId} ${customerName} ${statusText}`;

            item.style.display = searchContent.includes(term) ? 'block' : 'none';
        });

        document.querySelectorAll('.order-item, table.w-full tr').forEach(el => {
            if (el.style.display !== 'none') {
                el.style.opacity = '1';
            }
        });
    }

    // Combine search with status filter using the search button if needed
    const searchButton = document.querySelector('.input-group .btn');

    if (searchButton) {
        searchButton.addEventListener('click', function (e) {
            e.preventDefault(); // Prevent form submission if using JS search
            const searchTerm = document.querySelector('.search-input').value.toLowerCase().trim();
            searchOrders(searchTerm);
            updateOrderCount();
        });
    }

    // Add event listener for refresh button in empty state
    const refreshButton = document.querySelector('.text-center .btn-primary');
    if (refreshButton) {
        refreshButton.addEventListener('click', function () {
            location.reload();
        });
    }

    // Pull-to-refresh functionality
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

    // Replace existing order row click listeners with this:
    document.querySelectorAll('tr[data-order-id], .order-item').forEach(row => {
        row.addEventListener('click', function (e) {
            // Prevent modal opening when clicking buttons
            if (e.target.closest('button') || e.target.tagName === 'A') return;

            const orderId = this.dataset.orderId;
            loadOrderDetails(orderId);
        });
    });

    // Add click/touch listeners to mobile order items
    document.querySelectorAll('.mobile-order-list .order-item').forEach(function (item) {
        item.addEventListener('click', function () {
            const orderId = this.getAttribute('data-order-id');
            console.log("Clicked Order ID:", orderId); // Debugging
            loadOrderDetails(orderId);
        });

        item.addEventListener('touchstart', function () {
            const orderId = this.getAttribute('data-order-id');
            console.log("Touched Order ID:", orderId); // Debugging
            loadOrderDetails(orderId);
        });
    });

    updateOrderCount();
});

// function loadOrderDetails(orderId) {
//     console.log("Loading details for order:", orderId);
//     const modalContent = document.getElementById('order-details-content');
//     const summaryContent = document.getElementById('order-summary');
//     modalContent.innerHTML = '<p>Loading order details...</p>';
//     summaryContent.innerHTML = '';

//     fetch('/store-admin/order-details/' + orderId + '/')
//         .then(response => {
//             if (!response.ok) {
//                 throw new Error("HTTP error " + response.status);
//             }
//             return response.json();
//         })
//         .then(data => {
//             console.log("Received order details data:", data);
//             if (data.error) {
//                 modalContent.innerHTML = '<p>' + data.error + '</p>';
//                 return;
//             }
//             // Build HTML for order items table
//             let itemsHtml = '<h6>Order #' + orderId + '</h6>';
//             itemsHtml += '<table class="table table-bordered">';
//             itemsHtml += '<thead><tr><th>Product ID</th><th>Product Name</th><th>Quantity</th><th>Unit Price</th></tr></thead>';
//             itemsHtml += '<tbody>';
//             data.items.forEach(function (item) {
//                 itemsHtml += '<tr>';
//                 itemsHtml += '<td>' + item.product_id + '</td>';
//                 itemsHtml += '<td>' + item.product_name + '</td>';
//                 itemsHtml += '<td>' + item.quantity + '</td>';
//                 itemsHtml += '<td>₹' + item.price + '</td>';
//                 itemsHtml += '</tr>';
//             });
//             itemsHtml += '</tbody></table>';
//             modalContent.innerHTML = itemsHtml;

//             // Calculate selling price if not provided by the backend
//             let sellingPrice = data.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);

//             // Build HTML for price breakdown summary
//             let summaryHtml = '<table class="table table-bordered">';
//             summaryHtml += '<tbody>';
//             summaryHtml += '<tr><th>Selling Price</th><td>₹' + sellingPrice.toFixed(2) + '</td></tr>';
//             summaryHtml += '<tr><th>Discount</th><td>₹' + data.discount_rate + '</td></tr>';
//             summaryHtml += '<tr><th>Shipping Rate</th><td>₹' + data.shipping_rate + '</td></tr>';
//             summaryHtml += '<tr><th>Total Price</th><td>₹' + data.order_total + '</td></tr>';
//             summaryHtml += '</tbody></table>';
//             summaryContent.innerHTML = summaryHtml;

//             // Show the modal using Bootstrap's Modal API
//             var orderDetailsModal = new bootstrap.Modal(document.getElementById('orderDetailsModal'));
//             orderDetailsModal.show();
//         })
//         .catch(error => {
//             modalContent.innerHTML = '<p>Error loading order details.</p>';
//             console.error('Error fetching order details:', error);
//         });
// }

function loadOrderDetails(orderId) {
    const modal = document.getElementById('orderDetailsModal');
    const modalContent = document.getElementById('order-details-content');
    const summaryContent = document.getElementById('order-summary');

    // Show loading state
    modalContent.innerHTML = `
      <div class="py-8 text-center space-y-3">
        <div class="animate-spin text-3xl text-accent-secondary">
          <i class="fas fa-spinner"></i>
        </div>
        <p class="text-gray-400">Loading order details...</p>
      </div>
    `;

    // Show modal with transition
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.dataset.state = 'visible';
    }, 50);

    fetch(`/store-admin/order-details/${orderId}/`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Build order items table (your existing code)
            let itemsHtml = `
          <div class="space-y-4">
            <div class="flex items-center justify-between text-sm text-gray-400">
              <span>Order ID: #${orderId}</span>
              <span>${new Date(data.timestamp).toLocaleDateString()}</span>
            </div>
            
            <div class="space-y-3">
              <h4 class="text-lg font-semibold mb-2">Products</h4>
              <div class="divide-y divide-gray-700">
                ${data.items.map(item => `
                  <div class="order-item-row py-3 flex items-center justify-between hover:bg-navy transition-colors rounded-lg px-3">
                    <div class="flex-1">
                      <div class="font-medium">${item.product_name}</div>
                      <div class="text-sm text-gray-400">SKU: ${item.sku || 'N/A'}</div>
                    </div>
                    <div class="text-right">
                      <div>₹${item.price.toLocaleString()}</div>
                      <div class="text-sm text-gray-400">x ${item.quantity}</div>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
        `;

            // Build summary (your existing code)
            let summaryHtml = `
          <div class="space-y-2">
            <div class="flex justify-between">
              <span>Subtotal</span>
              <span>₹${data.order_total.toLocaleString()}</span>
            </div>
            <div class="flex justify-between text-gray-400">
              <span>Shipping</span>
              <span>₹${data.shipping_rate.toLocaleString()}</span>
            </div>
            <div class="pt-4 mt-4 border-t border-gray-700 flex justify-between font-semibold">
              <span>Total</span>
              <span>₹${(data.order_total + data.shipping_rate).toLocaleString()}</span>
            </div>
          </div>
        `;

            modalContent.innerHTML = itemsHtml;
            summaryContent.innerHTML = summaryHtml;
        })
        .catch(error => {
            modalContent.innerHTML = `
          <div class="text-center py-8 space-y-3 text-red-400">
            <i class="fas fa-exclamation-circle text-3xl"></i>
            <p class="text-sm">Error loading order details: ${error.message}</p>
            <button onclick="loadOrderDetails(${orderId})" 
                    class="mt-4 px-4 py-2 bg-navy rounded-lg hover:bg-opacity-80 transition">
              Retry
            </button>
          </div>
        `;
        });
}

function hideModal() {
    const modal = document.getElementById('orderDetailsModal');
    // Start hiding: remove the visible state
    modal.dataset.state = 'hidden';
    // After the transition duration (300ms per your CSS), add the hidden class
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}




// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function () {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn')
    const closeMobileMenuBtn = document.getElementById('closeMobileMenuBtn')
    const mobileMenu = document.querySelector('.mobile-menu')

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function () {
            mobileMenu.classList.add('open')
        })
    }

    if (closeMobileMenuBtn) {
        closeMobileMenuBtn.addEventListener('click', function () {
            mobileMenu.classList.remove('open')
        })
    }

    // Profile overlay
    const profileBtn = document.getElementById('profileBtn')
    const mobileProfileBtn = document.getElementById('mobileProfileBtn')
    const closeProfileBtn = document.getElementById('closeProfileBtn')
    const profileOverlay = document.getElementById('profileOverlay')

    if (profileBtn) {
        profileBtn.addEventListener('click', function () {
            profileOverlay.classList.remove('hidden')
        })
    }

    if (mobileProfileBtn) {
        mobileProfileBtn.addEventListener('click', function () {
            profileOverlay.classList.remove('hidden')
        })
    }

    if (closeProfileBtn) {
        closeProfileBtn.addEventListener('click', function () {
            profileOverlay.classList.add('hidden')
        })
    }

    // Close alerts
    const closeAlerts = document.querySelectorAll('.close-alert')
    closeAlerts.forEach((button) => {
        button.addEventListener('click', function () {
            this.parentElement.remove()
        })
    })

    // Order row click handler
    const orderRows = document.querySelectorAll('.order-row, .order-item')
    const orderDetailsModal = document.getElementById('orderDetailsModal')
    const closeOrderDetailsBtn = document.getElementById('closeOrderDetailsBtn')
    const closeOrderDetailsFooterBtn = document.getElementById('closeOrderDetailsFooterBtn')

    orderRows.forEach((row) => {
        row.addEventListener('click', function (e) {
            // Don't open modal if clicking on buttons
            if (e.target.tagName === 'BUTTON' || e.target.closest('button') || e.target.tagName === 'A' || e.target.closest('a')) {
                return
            }

            const orderId = this.dataset.orderId
            // Here you would fetch order details and populate the modal
            // For now, just show the modal
            orderDetailsModal.classList.remove('hidden')
        })
    })

    if (closeOrderDetailsBtn) {
        closeOrderDetailsBtn.addEventListener('click', function () {
            orderDetailsModal.classList.add('hidden')
        })
    }

    if (closeOrderDetailsFooterBtn) {
        closeOrderDetailsFooterBtn.addEventListener('click', function () {
            orderDetailsModal.classList.add('hidden')
        })
    }

    // Status filter functionality
    const statusFilter = document.getElementById('statusFilter')
    if (statusFilter) {
        statusFilter.addEventListener('change', function () {
            // Here you would implement filtering logic
            console.log('Filter changed:', this.value)
            // For a quick demo, you could submit a form or redirect
            // window.location.href = `?status=${this.value}`;
        })
    }
})

document.addEventListener('DOMContentLoaded', function () {
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
        }, 300); // Match transition duration

    }
});
