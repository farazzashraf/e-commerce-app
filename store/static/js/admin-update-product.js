document.addEventListener('DOMContentLoaded', () => {
    const updateProductForm = document.getElementById('updateProductForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const successMessage = document.getElementById('successMessage');
    const errorContainer = document.getElementById('errorContainer');

    if (updateProductForm) {
        updateProductForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent form submission

            // Clear previous error messages
            errorContainer.style.display = 'none';
            errorContainer.textContent = '';

            // Show loading spinner
            loadingOverlay.style.display = 'flex';

            // Create a FormData object to handle file uploads
            const formData = new FormData(updateProductForm);

            // Log FormData contents for debugging
            const formDataEntries = Array.from(formData.entries());
            console.log('Form Data Entries:', formDataEntries);

            // Perform client-side validation
            const name = formData.get('name').trim();
            const category = formData.get('category');
            const price = formData.get('price').trim();
            const description = formData.get('description').trim();
            const image = formData.get('image');

            if (!name || !category || !price || !description) {
                errorContainer.textContent = 'All fields are required except for the image.';
                errorContainer.style.display = 'block';
                loadingOverlay.style.display = 'none'; // Hide loading spinner
                return;
            }

            if (isNaN(price) || parseFloat(price) <= 0) {
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

                if (response.ok) {
                    const result = await response.json();
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
