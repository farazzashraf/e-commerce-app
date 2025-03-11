import { auth, googleProvider } from "./firebase-config.js";
import { signInWithEmailAndPassword, sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-auth.js";
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
                // Check if a redirect URL is provided (for admin users)
                if (data.redirect) {
                    console.log("🚀 Redirecting to admin dashboard...");
                    window.location.replace(data.redirect);
                } else {
                    console.log("🚀 Redirecting to home page...");
                    window.location.replace("/");
                }
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

    // Forgot Password Modal Handling
    const forgotPasswordLink = document.getElementById("forgotPasswordLink");
    const forgotPasswordModal = document.getElementById("forgotPasswordModal");
    const closeModal = document.querySelector(".close");
    const resetPasswordBtn = document.getElementById("resetPasswordBtn");
    const resetEmailInput = document.getElementById("resetEmail");
    const resetMessage = document.getElementById("resetMessage");

    // Ensure the modal is hidden when the page loads
    forgotPasswordModal.style.display = "none";

    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener("click", function (e) {
            e.preventDefault();
            forgotPasswordModal.style.display = "flex";
        });
    }

    // Close modal when clicking the close button
    if (closeModal) {
        closeModal.addEventListener("click", function () {
            forgotPasswordModal.style.display = "none";
        });
    }


    window.addEventListener("click", function (event) {
        if (event.target === forgotPasswordModal) {
            forgotPasswordModal.style.display = "none";
        }
    });

    resetPasswordBtn.addEventListener("click", async function () {
        const email = resetEmailInput.value.trim();
        if (!email) {
            resetMessage.style.color = "red";
            resetMessage.textContent = "Please enter a valid email.";
            return;
        }

        resetPasswordBtn.disabled = true;
        resetPasswordBtn.innerText = "Checking...";

        // ✅ Step 1: Check if email exists in Supabase before sending reset link
        const emailExists = await isEmailRegistered(email);
        if (!emailExists) {
            resetMessage.style.color = "red";
            resetMessage.textContent = "Email not registered.";
            resetPasswordBtn.disabled = false;
            resetPasswordBtn.innerText = "Send Reset Link";
            return;
        }

        resetPasswordBtn.innerText = "Sending...";

        try {
            await sendPasswordResetEmail(auth, email);
            resetMessage.style.color = "green";
            resetMessage.textContent = "Reset link sent! Check your email.";
        } catch (error) {
            console.error("Password Reset Error:", error);
            resetMessage.style.color = "red";
            if (error.code === "auth/user-not-found") {
                resetMessage.textContent = "Email not registered.";
            } else {
                resetMessage.textContent = "Failed to send reset link. Try again.";
            }
        } finally {
            resetPasswordBtn.disabled = false;
            resetPasswordBtn.innerText = "Send Reset Link";
        }
    });
});

// Function to check if email exists in Supabase
async function isEmailRegistered(email) {
    try {
        const response = await fetch("/check-email/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ email }),
        });

        const data = await response.json();
        return data.exists; // Returns true if email is found, false otherwise
    } catch (error) {
        console.error("Error checking email:", error);
        return false; // Assume email is not found in case of error
    }
}