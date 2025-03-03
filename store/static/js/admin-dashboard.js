// function showDeleteModal(productId) {
//     const deleteModal = document.getElementById('deleteModal');
//     const deleteForm = document.getElementById('deleteForm');

//     // ✅ Correct: This matches the Django URL pattern
//     deleteForm.action = `/store-admin/delete-product/${productId}/`;

//     deleteModal.classList.remove('hidden');  // Show modal
// }

function showDeleteModal(productId) {
    const modal = document.getElementById('deleteModal');
    const form = document.getElementById('deleteForm');
    form.action = `/admin/delete-product/${productId}/`;
    modal.classList.remove('hidden');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
}