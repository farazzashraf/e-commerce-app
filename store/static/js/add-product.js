document.addEventListener('DOMContentLoaded', () => {
    const addProductForm = document.getElementById('addProductForm');
    const errorContainer = document.getElementById('errorContainer');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const successMessage = document.getElementById('successMessage');

    addProductForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent form submission

        // Clear previous error messages
        errorContainer.style.display = 'none';
        errorContainer.textContent = '';

        // Show loading spinner
        loadingOverlay.style.display = 'flex';

        // Create a FormData object to handle file uploads
        const formData = new FormData(addProductForm);

        // Log FormData contents
        const formDataEntries = Array.from(formData.entries());
        console.log('Form Data Entries:', formDataEntries);

        // Perform client-side validation
        const name = formData.get('name').trim();
        const category = formData.get('category'); // Get category value
        const price = formData.get('price').trim();
        const originalPrice = formData.get('originalprice').trim();
        const description = formData.get('description').trim();
        const image = formData.get('image');

        if (!name || !category || !price || !originalPrice || !description || !image) {
            errorContainer.textContent = 'All fields are required.';
            errorContainer.style.display = 'block';
            loadingOverlay.style.display = 'none';
            return;
        }

        if (isNaN(price) || parseFloat(price) <= 0) {
            errorContainer.textContent = 'Please enter a valid price.';
            errorContainer.style.display = 'block';
            return;
        }

        try {
            // Send form data to the server
            const response = await fetch(addProductForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'), // Get CSRF token
                },
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // alert('Product added successfully!');
                    // Show success message
                    successMessage.style.display = 'block';
                    // window.location.href = '/store-admin/dashboard'; // Adjust the redirect URL
                    // Redirect after 2 seconds
                    setTimeout(() => {
                        window.location.href = '/store-admin/dashboard';
                    }, 1500);
                } else {
                    console.error('Error Response:', result);
                    throw new Error(result.message || 'Failed to add product.');
                }
            } else {
                const error = await response.json();
                console.error('Error Response:', error);
                throw new Error(error.message || 'An error occurred while adding the product.');
            }

        } catch (error) {
            errorContainer.textContent = error.message;
            errorContainer.style.display = 'block';
        } finally {
            loadingOverlay.style.display = 'none'; // Hide loading spinner
        }
    });

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

document.addEventListener('DOMContentLoaded', function () {
    const addMoreBtn = document.getElementById('addMoreImages');
    const additionalImagesContainer = document.getElementById('additionalImagesContainer');

    addMoreBtn.addEventListener('click', function () {
        // Count existing additional image file inputs
        const currentInputs = additionalImagesContainer.querySelectorAll('input[name="additional_images"]').length;
        if (currentInputs >= 3) {
            alert("You can only add up to 3 additional images.");
            return;
        }
        const input = document.createElement('input');
        input.type = 'file';
        input.name = 'additional_images'; // In your backend, you can use request.FILES.getlist('additional_images')
        input.accept = 'image/*';
        input.className = 'border border-gray-300 p-2 w-full mb-2';
        additionalImagesContainer.appendChild(input);
    });
});

// Function to fetch categories from the server
async function fetchCategories() {
    try {
        const response = await fetch('/api/categories/');
        if (!response.ok) {
            throw new Error('Failed to fetch categories');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching categories:', error);
        return [];
    }
}

async function fetchSubcategories(categoryId) {
    try {
        // Correct the URL here to match your Django URL configuration.
        const response = await fetch(`/api/categories/${categoryId}/subcategories/`);
        if (!response.ok) {
            throw new Error('Failed to fetch subcategories');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching subcategories:', error);
        return [];
    }
}


// Function to populate the category dropdown
function populateCategoryDropdown(categories) {
    const categorySelect = document.getElementById('category');
    
    // Clear existing options except the first one
    while (categorySelect.options.length > 1) {
        categorySelect.remove(1);
    }
    
    // Add new options
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        categorySelect.appendChild(option);
    });
}

// Function to populate the subcategory dropdown
function populateSubcategoryDropdown(subcategories) {
    const subcategorySelect = document.getElementById('subcategory');
    
    // Clear existing options
    subcategorySelect.innerHTML = '';
    
    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Select a Subcategory';
    defaultOption.disabled = true;
    defaultOption.selected = true;
    subcategorySelect.appendChild(defaultOption);
    
    // Add new options
    subcategories.forEach(subcategory => {
        const option = document.createElement('option');
        option.value = subcategory.id;
        option.textContent = subcategory.name;
        subcategorySelect.appendChild(option);
    });
}

// Initialize categories and subcategories
document.addEventListener('DOMContentLoaded', async () => {
    // Get the category and subcategory select elements
    const categorySelect = document.getElementById('category');
    const subcategorySelect = document.getElementById('subcategory');
    
    // Fetch and populate categories
    const categories = await fetchCategories();
    populateCategoryDropdown(categories);
    
    // Add event listener for category change
    categorySelect.addEventListener('change', async (event) => {
        const categoryId = event.target.value;
        if (categoryId) {
            // Fetch and populate subcategories based on selected category
            const subcategories = await fetchSubcategories(categoryId);
            populateSubcategoryDropdown(subcategories);
            
            // Enable subcategory select
            subcategorySelect.disabled = false;
        } else {
            // Reset subcategory select if no category is selected
            subcategorySelect.innerHTML = '<option value="" disabled selected>Select a Category First</option>';
            subcategorySelect.disabled = true;
        }
    });
});