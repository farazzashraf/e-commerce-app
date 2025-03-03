import { auth } from "./firebase-config.js"; // Import Firebase

// Function to get CSRF token from cookies
function getCsrfToken() {
    const csrfToken = document.cookie.match(/csrftoken=([\w-]+)/);
    return csrfToken ? csrfToken[1] : null;
}

document.addEventListener("DOMContentLoaded", function () {
    const logoutButton = document.querySelector('.logout-btn');

    if (logoutButton) {
        logoutButton.addEventListener('click', async function (event) {
            event.preventDefault();  // Prevent default link behavior

            try {
                // ✅ Sign out from Firebase first (if user is logged in)
                await auth.signOut();
                console.log("✅ Firebase user signed out");

                // ✅ Send logout request to Django backend
                const response = await fetch('/logout/', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken(), // Use safe CSRF token retrieval
                    },
                });

                if (response.ok) {
                    console.log("✅ Django session cleared");
                    window.location.href = '/login/';  // ✅ Redirect to login page
                } else {
                    console.error("❌ Logout failed on the server.");
                }
            } catch (error) {
                console.error("❌ Error during logout:", error);
            }
        });
    }
});
