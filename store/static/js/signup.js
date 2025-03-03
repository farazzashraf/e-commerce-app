import { auth } from "./firebase-config.js";
import { createUserWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-auth.js";

document.addEventListener("DOMContentLoaded", function () {
    const signupButton = document.getElementById("signupButton");
    const errorMessage = document.getElementById("errorMessage");
    const successMessage = document.getElementById("successMessage");
    const passwordInput = document.getElementById("password");
    const confirmPasswordInput = document.getElementById("confirmPassword");
    const togglePassword = document.querySelector(".toggle-password");
    const spinner = document.querySelector(".spinner");

    if (!signupButton || !passwordInput || !confirmPasswordInput) {
        console.error("❌ Required elements not found in DOM!");
        return;
    }

    // Initially hide spinner
    if (spinner) spinner.style.display = "none";

    function isValidEmail(email) {
        const emailRegex = /^[a-zA-Z0-9._+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
        return emailRegex.test(email);
    }

    togglePassword.addEventListener("click", function () {
        if (passwordInput.type === "password") {
            passwordInput.type = "text";
            togglePassword.innerHTML = '<i class="fas fa-eye-slash"></i>';
        } else {
            passwordInput.type = "password";
            togglePassword.innerHTML = '<i class="fas fa-eye"></i>';
        }
    });

    signupButton.addEventListener("click", async (event) => {
        event.preventDefault();

        const name = document.getElementById("name").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const email = document.getElementById("email").value.trim();
        const password = passwordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();

        // Clear previous errors
        errorMessage.style.display = "none";
        errorMessage.innerText = "";

        if (!name || !phone || !email || !password || !confirmPassword) {
            errorMessage.innerText = "All fields are required.";
            errorMessage.style.display = "block";
            return;
        }

        if (password !== confirmPassword) {
            errorMessage.innerText = "Passwords do not match!";
            errorMessage.style.display = "block";
            return;
        }

        if (!isValidEmail(email)) {
            errorMessage.innerText = "Invalid email format!";
            errorMessage.style.display = "block";
            return;
        }

        // Show loading spinner
        signupButton.disabled = true;
        signupButton.querySelector(".button-text").innerText = "Signing up...";
        if (spinner) spinner.style.display = "inline-block";

        try {
            // 🔹 Check if email is already registered (via Django)
            const response = await fetch('/check-email/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                },
                body: JSON.stringify({ email: email })
            });

            const result = await response.json();
            if (!result.success) {
                errorMessage.innerText = result.error;
                errorMessage.style.display = "block";
                return;
            }

            // 🔹 Register user in Firebase
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            console.log("✅ User signed up:", userCredential.user);

            const user = userCredential.user;
            console.log("✅ UID:", user.uid);

            // 🔹 Send user details to Django backend
            const userData = { uid: user.uid, name, phone, email };
            console.log("🚀 Sending user data to backend:", userData);

            const backendResponse = await fetch('/signup/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                },
                body: JSON.stringify(userData)
            });

            const backendResult = await backendResponse.json();
            console.log("Backend Response:", backendResult);

            if (!backendResult.success) {
                errorMessage.innerText = backendResult.error;
                errorMessage.style.display = "block";
                return;
            }

            // ✅ Success! Show message & redirect
            successMessage.innerText = "Account created successfully! Redirecting...";
            errorMessage.style.display = "none";

            setTimeout(() => {
                window.location.href = "/login";
            }, 2000);

        } catch (error) {
            console.error("❌ Error:", error.message);
            errorMessage.innerText = error.message;
            errorMessage.style.display = "block";
        } finally {
            // Hide spinner & reset button
            signupButton.disabled = false;
            signupButton.querySelector(".button-text").innerText = "Sign Up";
            if (spinner) spinner.style.display = "none";
        }
    });
});
