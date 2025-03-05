import { auth } from "./firebase-config.js";
import { createUserWithEmailAndPassword, sendEmailVerification } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-auth.js";

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

    if (spinner) spinner.style.display = "none"; // Hide spinner initially

    function isValidEmail(email) {
        const emailRegex = /^[a-zA-Z0-9._+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
        return emailRegex.test(email);
    }

    function checkPasswordStrength(password) {
        let strength = 0;
        if (password.length >= 8) strength++; // ✅ 8+ characters
        if (/[A-Z]/.test(password)) strength++; // ✅ Uppercase
        if (/[a-z]/.test(password)) strength++; // ✅ Lowercase
        if (/\d/.test(password)) strength++; // ✅ Number
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++; // ✅ Special character
        return strength;
    }

    function isStrongPassword(password) {
        return checkPasswordStrength(password) === 5;
    }

    togglePassword.addEventListener("click", function () {
        passwordInput.type = passwordInput.type === "password" ? "text" : "password";
        togglePassword.innerHTML = passwordInput.type === "password" ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
    });

    signupButton.addEventListener("click", async (event) => {
        event.preventDefault();

        const name = document.getElementById("name").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const email = document.getElementById("email").value.trim();
        const password = passwordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();

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

        if (!isStrongPassword(password)) {
            errorMessage.innerText = "Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.";
            errorMessage.style.display = "block";
            return;
        }

        if (!isValidEmail(email)) {
            errorMessage.innerText = "Invalid email format!";
            errorMessage.style.display = "block";
            return;
        }

        signupButton.disabled = true;
        signupButton.querySelector(".button-text").innerText = "Signing up...";
        if (spinner) spinner.style.display = "inline-block";

        try {
            // 🔹 Check if email is already registered in Django
            const response = await fetch('/check-email/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                },
                body: JSON.stringify({ email })
            });

            const result = await response.json();
            if (!result.success) {
                errorMessage.innerText = result.error;
                errorMessage.style.display = "block";
                return;
            }

            // 🔹 Register user in Firebase
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            const user = userCredential.user;
            console.log("✅ Firebase signup successful:", user.uid);

            await sendEmailVerification(user);
            console.log("📧 Verification email sent!");

            successMessage.innerText = "Verification email sent! Please verify before logging in.";
            successMessage.style.display = "block";

            // 🔹 Wait for email verification
            const checkVerification = async () => {
                while (!user.emailVerified) {
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    await user.reload();
                }

                console.log("✅ Email verified! Proceeding with backend registration...");

                // 🔹 Register user in Supabase via Django
                const backendResponse = await fetch('/signup/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                    },
                    body: JSON.stringify({ uid: user.uid, name, phone, email })
                });

                const backendResult = await backendResponse.json();
                if (backendResult.success) {
                    successMessage.innerText = "Account verified and created successfully! Redirecting...";
                    setTimeout(() => window.location.href = "/login", 1500);
                } else {
                    errorMessage.innerText = backendResult.error;
                    errorMessage.style.display = "block";
                }
            };

            // Wait until the user verifies their email
            auth.onAuthStateChanged(async (user) => {
                if (user) {
                    await checkVerification();
                }
            });

        } catch (error) {
            console.error("❌ Error:", error.message);
            errorMessage.innerText = error.message;
            errorMessage.style.display = "block";
        } finally {
            signupButton.disabled = false;
            signupButton.querySelector(".button-text").innerText = "Sign Up";
            if (spinner) spinner.style.display = "none";
        }
    });
});
