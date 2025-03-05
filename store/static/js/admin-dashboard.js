function showDeleteModal(productId) {
    console.log("Product ID:", productId); // Debugging

    const modal = document.getElementById('deleteModal');
    const form = document.getElementById('deleteForm');

    if (!modal || !form) {
        console.error("Modal or form not found!");
        return;
    }

    form.action = `/store-admin/delete-product/${productId}/`;
    modal.style.display = "flex"; // Show modal
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.style.display = "none"; // Hide it properly
    }
}

function showImagesModal(button) {
    const imagesModal = document.getElementById("imagesModal");
    const imagesModalContent = document.getElementById("imagesModalContent");

    // Clear previous content
    imagesModalContent.innerHTML = "";

    // Get image URLs from the data attribute
    let imageUrls = button.getAttribute("data-image-urls").split(",");

    // Trim and filter empty values
    imageUrls = imageUrls.map(url => url.trim()).filter(url => url !== "");

    console.log('Processed URLs:', imageUrls); // Add this line

    if (imageUrls.length > 0) {
        imageUrls.forEach(url => {
            const imgElement = document.createElement("img");
            imgElement.src = url;
            imgElement.className = "w-32 h-32 object-cover rounded-lg shadow-sm border border-gray-200 m-2";
            imagesModalContent.appendChild(imgElement);
        });

        imagesModal.classList.remove("hidden");
    } else {
        alert("No images available.");
    }
}

function closeImagesModal() {
    document.getElementById("imagesModal").classList.add("hidden");
}
