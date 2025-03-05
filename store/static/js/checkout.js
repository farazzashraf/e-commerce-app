document.addEventListener("DOMContentLoaded", function () {
    const checkoutForm = document.querySelector("form");
    const subtotalElement = document.getElementById("subtotal-price");
    const shippingElement = document.getElementById("shipping-price"); // ✅ Added
    const discountElement = document.getElementById("discount-amount");
    const finalTotalElement = document.getElementById("final-total-price");

    // Extract values from the page
    let subtotal = parseFloat(subtotalElement.textContent.replace("₹", "")) || 0;
    let shipping = parseFloat(shippingElement.textContent.replace("₹", "")) || 0; // ✅ Added
    let discountAmount = parseFloat(discountElement.textContent.replace("-₹", "")) || 0;
    let finalTotal = subtotal + shipping - discountAmount;

    // Update Final Total in UI
    finalTotalElement.textContent = `₹${finalTotal.toFixed(2)}`;

    checkoutForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const formData = new FormData(checkoutForm);
        let formObject = {};
        formData.forEach((value, key) => {
            formObject[key] = value.trim();
        });

        const orderData = {
            payment_method: formObject["payment_method"],
            address: {
                name: formObject["name"],
                mobile: formObject["mobile"],
                pincode: formObject["pincode"],
                house_no: formObject["house_no"],
                street: formObject["street"],
                city: formObject["city"],
                state: formObject["state"],
                country: formObject["country"],
            },
            subtotal: subtotal,
            shipping: shipping,  // ✅ Added
            discount: discountAmount,  // ✅ Fixed variable name
            total: finalTotal
        };

        console.log("📦 Sending Order Data:", orderData);

        try {
            let response = await fetch("/place-order/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(orderData)
            });

            let data = await response.json();
            console.log("✅ Order Response:", data);

            if (response.ok) {
                // alert(data.success);
                window.location.href = "/order-success/";
            } else {
                // Enhanced Error Modal
                showErrorModal(data.error || "Order failed. Please try again.");
            }
        } catch (error) {
            console.error("❌ Error:", error);
            showErrorModal("Something went wrong. Please try again.");
        }
    });

    // Enhanced Error Modal Function
    function showErrorModal(message) {
        // Create modal container
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = `
            <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
                <div class="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full mx-4 animate-pop-in">
                    <div class="flex items-center justify-center mb-4">
                        <svg class="w-16 h-16 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <h2 class="text-xl font-bold text-center text-gray-800 mb-4">Order Error</h2>
                    <p class="text-gray-600 text-center mb-6">${message}</p>
                    <div class="flex justify-center">
                        <button id="close-error-modal" class="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add to body
        document.body.appendChild(modalContainer);

        // Close modal functionality
        const closeButton = modalContainer.querySelector('#close-error-modal');
        closeButton.addEventListener('click', () => {
            modalContainer.remove();
        });

        // Close on outside click
        modalContainer.addEventListener('click', (e) => {
            if (e.target === modalContainer) {
                modalContainer.remove();
            }
        });
    }
});
