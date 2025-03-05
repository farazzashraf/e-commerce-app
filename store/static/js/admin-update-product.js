document.addEventListener('DOMContentLoaded', () => {
    const updateProductForm = document.getElementById('updateProductForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const successMessage = document.getElementById('successMessage');
    const errorContainer = document.getElementById('errorContainer');

    if (updateProductForm) {
        updateProductForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent form submission

            console.log("🔥 Form submitted! Preparing request...");

            // Clear previous error messages
            errorContainer.style.display = 'none';
            errorContainer.textContent = '';

            // Show loading spinner
            loadingOverlay.style.display = 'flex';

            // Create FormData object
            const formData = new FormData(updateProductForm);
            console.log("📂 Form Data Entries:", [...formData.entries()]);

            // Perform client-side validation
            const name = formData.get('name').trim();
            const category = formData.get('category');
            const price = formData.get('price').trim();
            const originalPrice = formData.get('originalprice').trim();
            const description = formData.get('description').trim();
            const image = formData.get('image');

            // Collect files from inputs with names like "additional_image_1", "additional_image_2", etc.
            const additionalImageInputs = document.querySelectorAll('input[name^="additional_image_"]');
            additionalImageInputs.forEach(input => {
                if (input.files.length > 0) {
                    // Append the file using the input's unique name as the key.
                    formData.append(input.name, input.files[0]);
                }
            });

            if (!name || !category || !price || !originalPrice || !description) {
                errorContainer.textContent = 'All fields are required except for the image.';
                errorContainer.style.display = 'block';
                loadingOverlay.style.display = 'none'; // Hide loading spinner
                return;
            }

            if (isNaN(price) || parseFloat(price) <= 0 || isNaN(originalPrice) || parseFloat(originalPrice) <= 0) {
                errorContainer.textContent = 'Please enter a valid price.';
                errorContainer.style.display = 'block';
                loadingOverlay.style.display = 'none'; // Hide loading spinner
                return;
            }

            try {
                // Send form data to the server
                const response = await fetch(updateProductForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'), // Get CSRF token
                    },
                });

                console.log("🌍 Request sent to:", updateProductForm.action);

                if (response.ok) {
                    const result = await response.json();
                    console.log("✅ Server Response:", result);
                    if (result.success) {
                        // Show success message
                        successMessage.style.display = 'block';

                        // Redirect after 2 seconds
                        setTimeout(() => {
                            window.location.href = '/store-admin/dashboard';
                        }, 1500);
                    } else {
                        console.error('Error Response:', result);
                        throw new Error(result.message || 'Failed to update product.');
                    }
                } else {
                    const error = await response.json();
                    console.error('Error Response:', error);
                    throw new Error(error.message || 'An error occurred while updating the product.');
                }
            } catch (error) {
                errorContainer.textContent = error.message;
                errorContainer.style.display = 'block';
            } finally {
                loadingOverlay.style.display = 'none'; // Hide loading spinner
            }
        });
    } else {
        console.error('Update product form not found in the DOM.');
    }

    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});