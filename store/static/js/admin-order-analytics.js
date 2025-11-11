document.addEventListener("DOMContentLoaded", () => {
    // Fetch analytics data from the endpoint (which retrieves the current seller's data from the DB)
    fetch('/api/seller-analytics/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            console.log("Seller Analytics Data:", data);

            // Update stat cards (ensure your HTML has these placeholder classes)
            const totalOrdersElem = document.querySelector('.total-orders-count');
            const totalRevenueElem = document.querySelector('.total-revenue');
            const avgOrderValueElem = document.querySelector('.avg-order-value');
            const totalItemsSoldElem = document.querySelector('.total-items-sold');

            if (totalOrdersElem) totalOrdersElem.textContent = data.total_orders;
            if (totalRevenueElem) totalRevenueElem.textContent = `₹${data.total_revenue.toFixed(2)}`;
            if (avgOrderValueElem) avgOrderValueElem.textContent = `₹${data.avg_order_value.toFixed(2)}`;
            if (totalItemsSoldElem) totalItemsSoldElem.textContent = data.total_items_sold;

            // Update Order Status Distribution Doughnut Chart
            const statusLabels = data.orders_by_status.map(item => item.status);
            const statusCounts = data.orders_by_status.map(item => item.count);

            const orderStatusCanvas = document.getElementById('orderStatusChart');
            if (orderStatusCanvas) {
                const ctx = orderStatusCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: statusLabels,
                        datasets: [{
                            data: statusCounts,
                            backgroundColor: ['#4ade80', '#60a5fa', '#fbbf24', '#f87171'] // Adjust colors as needed
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
            }

            // Optionally, update Top Selling Products Chart (if you have a canvas with id "topProductsChart")
            const topProductsCanvas = document.getElementById('topProductsChart');
            if (topProductsCanvas) {
                const topProductsLabels = data.top_products.map(item => item.product_id__name);
                const topProductsQuantities = data.top_products.map(item => item.total_quantity);
                const ctx2 = topProductsCanvas.getContext('2d');
                new Chart(ctx2, {
                    type: 'bar',
                    data: {
                        labels: topProductsLabels,
                        datasets: [{
                            label: 'Quantity Sold',
                            data: topProductsQuantities,
                            backgroundColor: 'rgba(99, 102, 241, 0.8)' // Tailwind Indigo-500 with opacity
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.error("Error fetching seller analytics data:", error);
        });
});
