import { auth } from "./firebase-config.js";
import { signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-auth.js";

// Function to get the CSRF token from the cookie
function getCsrfToken() {
    const csrfToken = document.cookie.match(/csrftoken=([\w-]+)/);
    return csrfToken ? csrfToken[1] : null;
}

document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('adminLoginForm');
    const emailInput = document.getElementById('emailInput');
    const passwordInput = document.getElementById('passwordInput');
    const submitButton = document.getElementById('submitButton');
    const errorContainer = document.getElementById('errorContainer');

    function showError(message) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
        errorContainer.style.opacity = '1';
    }

    function hideError() {
        errorContainer.style.display = 'none';
        errorContainer.style.opacity = '0';
    }

    function setLoading(isLoading) {
        submitButton.disabled = isLoading;
        submitButton.innerHTML = isLoading ? '<span class="spinner"></span> Logging in...' : 'Login';
    }

    const togglePassword = document.getElementById("togglePassword");

    togglePassword.addEventListener("click", function () {
        if (passwordInput.type === "password") {
            passwordInput.type = "text";
            togglePassword.innerHTML = '<i class="fas fa-eye-slash"></i>'; // Change icon to "hide"
        } else {
            passwordInput.type = "password";
            togglePassword.innerHTML = '<i class="fas fa-eye"></i>'; // Change icon to "show"
        }
    });

    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        hideError(); // Remove this if you want the error to persist until successful login

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        if (!email || !password) {
            showError('Please fill in all fields');
            return;
        }

        setLoading(true);
        console.log("🔵 Sending request to /store-admin/login/ with method POST");

        try {
            // Sign in with Firebase Authentication
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            const user = userCredential.user;
            console.log("✅ Logged in Firebase User:", user);
            const idToken = await user.getIdToken(); // 🔥 Get Firebase ID token

            console.log("✅ Firebase ID Token:", idToken);

            const response = await fetch('/store-admin/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken() // Send CSRF token here
                },
                body: JSON.stringify({ token: idToken })
            });

            const data = await response.json();

            if (response.ok) {
                console.log("✅ Login successful! Redirecting...");
                hideError(); // Hide error only on successful login
                window.location.href = data.redirect; // Redirect to admin dashboard
            } else {
                console.error("❌ Login failed:", data.error);
                if (response.status === 401) {
                    showError("Invalid email or password. Please try again.");
                } else {
                    showError(data.error || "An error occurred. Please try again.");
                }
            }
        } catch (error) {
            console.error("❌ Firebase login error:", error);
            showError("Invalid email or password.");
        } finally {
            setLoading(false);
        }
    });
});
