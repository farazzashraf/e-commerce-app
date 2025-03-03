import { auth } from "./firebase-config.js";
import { signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-auth.js";

// Function to get the CSRF token from the cookie
function getCsrfToken() {
    const csrfToken = document.cookie.match(/csrftoken=([\w-]+)/);
    return csrfToken ? csrfToken[1] : null;
}

document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const errorMessageDiv = document.getElementById("errorMessage");
    const passwordInput = document.getElementById("password");
    const togglePassword = document.querySelector(".toggle-password");
    const loginButton = document.querySelector(".auth-button"); // ✅ Ensure login button is selected
    const spinner = document.querySelector(".spinner"); // ✅ Ensure spinner exists

    //  Hide spinner on page load
    if (spinner) spinner.style.display = "none";

    togglePassword.addEventListener("click", function () {
        if (passwordInput.type === "password") {
            passwordInput.type = "text";
            togglePassword.innerHTML = '<i class="fas fa-eye-slash"></i>'; // Change icon
        } else {
            passwordInput.type = "password";
            togglePassword.innerHTML = '<i class="fas fa-eye"></i>'; // Change icon back
        }
    });

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!email || !password) {
            errorMessageDiv.innerText = "Email and Password are required.";
            errorMessageDiv.style.display = "block";
            return;
        }

        // ✅ Show spinner when login starts
        loginButton.disabled = true;
        loginButton.querySelector(".button-text").innerText = "Logging in...";
        if (spinner) spinner.style.display = "inline-block";


        try {
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            const user = userCredential.user;
            console.log("✅ User signed in:", user);

            // ✅ Get Firebase token
            const idToken = await user.getIdToken();

            // Send token and CSRF token to Django backend
            const response = await fetch("/firebase-auth/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),  // Send CSRF token here
                },
                body: JSON.stringify({ token: idToken }),
            });

            const data = await response.json();
            console.log("Server Response:", data); // ✅ Debugging response

            if (data.success) {
                console.log("✅ Authentication successful!");
                console.log("🚀 Redirecting to home page...");

                // ✅ Set cookie via Django, not JavaScript
                window.location.replace("/home/");
            } else {
                console.error("❌ Backend authentication failed:", data.error);
                errorMessageDiv.innerText = `Authentication failed: ${data.error}`;
                errorMessageDiv.style.display = "block";
            }

        } catch (error) {
            console.error("❌ Firebase Error:", error);
            if (error.code === "auth/invalid-credential") {
                errorMessageDiv.innerText = "Invalid email or password.";
            } else if (error.code === "auth/user-not-found") {
                errorMessageDiv.innerText = "Email not registered.";
            } else if (error.code === "auth/wrong-password") {
                errorMessageDiv.innerText = "Incorrect password.";
            } else {
                errorMessageDiv.innerText = "An unexpected error occurred. Check console.";
            }

            errorMessageDiv.style.display = "block";

        } finally {
            // ✅ Hide spinner after login attempt
            loginButton.disabled = false;
            loginButton.querySelector(".button-text").innerText = "Sign In";
            if (spinner) spinner.style.display = "none";
        }
    });
});
