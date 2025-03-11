
document.addEventListener("DOMContentLoaded", function () {
    const statusFilter = document.getElementById("filter-status");
    const dateFilter = document.getElementById("filter-date");
    const priceFilter = document.getElementById("filter-price");
    const resetFilterBtn = document.getElementById("reset-filter");

    // Each order container has the class "animate-fade-in"
    const orderContainers = document.querySelectorAll(".animate-fade-in");

    function filterOrders() {
        const statusValue = statusFilter.value;
        const dateValue = dateFilter.value;  // Expected format: YYYY-MM-DD
        const priceValue = priceFilter.value;

        orderContainers.forEach(container => {
            let showContainer = true;

            // Filter by status
            if (statusValue !== "all") {
                if (container.getAttribute("data-status") !== statusValue) {
                    showContainer = false;
                }
            }

            // Filter by date: if a date is selected, compare with container's data-date attribute
            if (dateValue) {
                if (container.getAttribute("data-date") !== dateValue) {
                    showContainer = false;
                }
            }

            // Filter by price
            if (priceValue !== "all") {
                const priceElement = container.querySelector(".price");
                if (priceElement) {
                    // Remove the rupee sign and any commas, then convert to a float
                    let priceText = priceElement.textContent.replace("₹", "").replace(/,/g, "").trim();
                    let priceNumber = parseFloat(priceText);

                    if (priceValue === "low" && !(priceNumber < 500)) {
                        showContainer = false;
                    } else if (priceValue === "medium" && !(priceNumber >= 500 && priceNumber <= 2000)) {
                        showContainer = false;
                    } else if (priceValue === "high" && !(priceNumber > 2000)) {
                        showContainer = false;
                    }
                }
            }

            // Display or hide the container based on filter criteria
            container.style.display = showContainer ? "" : "none";
        });
    }

    // Event listeners for filter changes
    statusFilter.addEventListener("change", filterOrders);
    dateFilter.addEventListener("change", filterOrders);
    priceFilter.addEventListener("change", filterOrders);

    // Reset filters
    resetFilterBtn.addEventListener("click", function () {
        statusFilter.value = "all";
        dateFilter.value = "";
        priceFilter.value = "all";
        filterOrders();
    });
});