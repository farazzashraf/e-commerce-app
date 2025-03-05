import { auth } from "./firebase-config.js"; // Import Firebase

// Function to get CSRF token safely
function getCsrfToken() {
    return document.cookie.match(/csrftoken=([\w-]+)/)?.[1] ||
        document.querySelector("[name=csrfmiddlewaretoken]")?.value;
}

document.addEventListener("DOMContentLoaded", function () {
    const logoutButton = document.querySelector('.logout-btn');

    if (logoutButton) {
        logoutButton.addEventListener('click', async function (event) {
            event.preventDefault();  // Prevent default link behavior

            try {
                // ✅ Sign out from Firebase
                await auth.signOut();
                console.log("✅ Firebase user signed out");

                // ✅ Clear Django session
                const response = await fetch('/logout/', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken(),
                    },
                });

                if (response.ok) {
                    console.log("✅ Django session cleared");

                    // Set flag in sessionStorage to indicate logout
                    sessionStorage.setItem("loggedOut", "true");

                    // Redirect to login page without adding a new entry in the history
                    window.location.replace('/login/');
                } else {
                    console.error("❌ Logout failed on the server.");
                }
            } catch (error) {
                console.error("❌ Error during logout:", error);
            }
        });
    }

    // Only force reload if the user has logged out
    window.addEventListener("pageshow", function (event) {
        if (sessionStorage.getItem("loggedOut") === "true" && event.persisted) {
            console.log("🔄 Page loaded from cache after logout, forcing reload...");
            window.location.reload();
        }
    });
});
