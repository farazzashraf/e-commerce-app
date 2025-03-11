document.addEventListener("DOMContentLoaded", function () {
    console.log("Checkout JS loaded successfully!"); // Debug confirmation
    
    const checkoutForm = document.getElementById("checkout-form");
    const subtotalElement = document.getElementById("subtotal-price");
    const shippingElement = document.getElementById("shipping-price");
    const discountElement = document.getElementById("discount-amount");
    const finalTotalElement = document.getElementById("final-total-price");

    // Extract values from the page
    let subtotal = parseFloat(subtotalElement.textContent.replace("₹", "")) || 0;
    let shipping = parseFloat(shippingElement.textContent.replace("₹", "")) || 0;
    let discountAmount = parseFloat(discountElement.textContent.replace("-₹", "")) || 0;
    let finalTotal = subtotal + shipping - discountAmount;

    console.log("🛒 Subtotal:", subtotal);
    console.log("🚚 Shipping:", shipping);
    console.log("💰 Discount:", discountAmount);
    console.log("📦 Final Total:", finalTotal);

    // Update Final Total in UI
    finalTotalElement.textContent = `₹${finalTotal.toFixed(2)}`;

    checkoutForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        console.log("Form submitted - Processing overlay should appear");

        // Show processing overlay
        showProcessingOverlay();

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
            shipping: shipping || 99,
            discount: discountAmount || 0,
            total: finalTotal
        };

        console.log("📦 Sending Order Data:", orderData);

        try {
            // Update processing status
            updateProcessingStatus("Verifying your information...");

            // Artificial delay for better UX
            await new Promise(resolve => setTimeout(resolve, 800));

            updateProcessingStatus("Processing your payment...");

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
                // Success flow
                updateProcessingStatus("Order confirmed! Preparing your items...");

                // Add confetti effect
                showConfetti();

                // Redirect with delay for better UX
                setTimeout(() => {
                    window.location.href = "/order-success/";
                }, 1500);
            } else {
                // Remove processing overlay
                removeProcessingOverlay();
                // Show enhanced error modal
                showErrorModal(data.error || "Order failed. Please try again.");
            }
        } catch (error) {
            console.error("❌ Error:", error);
            removeProcessingOverlay();
            showErrorModal("Something went wrong. Please try again.");
        }
    });

    // Processing Overlay Function
    function showProcessingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'processing-overlay';
        overlay.innerHTML = `
            <div class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white bg-opacity-95">
                <div class="mb-8">
                    <svg class="w-16 h-16 animate-spin text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                </div>
                <h2 class="text-2xl font-bold text-gray-800 mb-2">Processing your order</h2>
                <p id="processing-status" class="text-lg text-gray-600">Please wait while we process your order...</p>
                <div class="mt-6 w-64 bg-gray-200 rounded-full h-2.5">
                    <div id="processing-progress" class="bg-indigo-600 h-2.5 rounded-full" style="width: 10%"></div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        // Animate progress bar
        animateProgressBar();
    }   

    function animateProgressBar() {
        const progressBar = document.getElementById('processing-progress');
        let width = 10;
        const interval = setInterval(() => {
            if (width >= 90) {
                clearInterval(interval);
            } else {
                width += 5;
                progressBar.style.width = width + '%';
            }
        }, 300);
    }

    function updateProcessingStatus(message) {
        const statusElement = document.getElementById('processing-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }

    function removeProcessingOverlay() {
        const overlay = document.getElementById('processing-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    // Confetti Function
    function showConfetti() {
        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.id = 'confetti-canvas';
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.pointerEvents = 'none';
        canvas.style.zIndex = '100';
        document.body.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        // Confetti particles
        const particles = [];
        const particleCount = 100;
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FCBF49', '#EF476F', '#FFD166'];

        // Create particles
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height - canvas.height,
                size: Math.random() * 10 + 5,
                color: colors[Math.floor(Math.random() * colors.length)],
                speed: Math.random() * 3 + 2,
                angle: Math.random() * 6.28,
                rotation: Math.random() * 0.2 - 0.1,
                rotationSpeed: Math.random() * 0.01
            });
        }

        // Animate confetti
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            let remainingParticles = 0;

            particles.forEach(p => {
                if (p.y < canvas.height) {
                    remainingParticles++;

                    ctx.save();
                    ctx.translate(p.x, p.y);
                    ctx.rotate(p.angle);

                    ctx.fillStyle = p.color;
                    ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);

                    ctx.restore();

                    p.y += p.speed;
                    p.x += Math.sin(p.angle) * 2;
                    p.angle += p.rotationSpeed;
                }
            });

            if (remainingParticles > 0) {
                requestAnimationFrame(animate);
            } else {
                canvas.remove();
            }
        }

        animate();
    }

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

        // Add custom animation
        const styleTag = document.createElement('style');
        styleTag.textContent = `
            @keyframes pop-in {
                0% { transform: scale(0.8); opacity: 0; }
                100% { transform: scale(1); opacity: 1; }
            }
            .animate-pop-in {
                animation: pop-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
            }
        `;
        document.head.appendChild(styleTag);

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