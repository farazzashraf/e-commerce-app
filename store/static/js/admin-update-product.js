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

document.addEventListener('DOMContentLoaded', async () => {
    const categorySelect = document.getElementById('category');
    const subcategorySelect = document.getElementById('subcategory');
  
    // Get preselected values from data attributes
    const selectedCategory = categorySelect.getAttribute('data-selected');
    const selectedSubcategory = subcategorySelect.getAttribute('data-selected');
  
    // Fetch and populate categories
    const categories = await fetchCategories();
    populateCategoryDropdown(categories);
  
    if (selectedCategory) {
      // Set the category select's value to the preselected value
      categorySelect.value = selectedCategory;
      // Fetch and populate subcategories for the selected category
      const subcategories = await fetchSubcategories(selectedCategory);
      populateSubcategoryDropdown(subcategories);
      subcategorySelect.disabled = false;
      if (selectedSubcategory) {
        // Set the subcategory select's value to the preselected subcategory
        subcategorySelect.value = selectedSubcategory;
      }
    } else {
      subcategorySelect.innerHTML = '<option value="" disabled selected>Select a Category First</option>';
      subcategorySelect.disabled = true;
    }
  
    // Add event listener for when the category changes
    categorySelect.addEventListener('change', async (event) => {
      const categoryId = event.target.value;
      if (categoryId) {
        const subcategories = await fetchSubcategories(categoryId);
        populateSubcategoryDropdown(subcategories);
        subcategorySelect.disabled = false;
      } else {
        subcategorySelect.innerHTML = '<option value="" disabled selected>Select a Category First</option>';
        subcategorySelect.disabled = true;
      }
    });
  });
  

