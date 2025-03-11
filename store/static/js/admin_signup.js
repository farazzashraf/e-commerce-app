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

    // Additional admin fields
    const companyLogoInput = document.getElementById("company_logo");
    const companyNameInput = document.getElementById("company_name");
    const shopAddressInput = document.getElementById("shop_address");
    const pincodeInput = document.getElementById("pincode");
    const phoneInput = document.getElementById("phone");
    const emailInput = document.getElementById("email");

    if (!signupButton || !passwordInput || !confirmPasswordInput) {
        console.error("❌ Required elements not found in DOM!");
        return;
    }

    if (spinner) spinner.style.display = "none"; // Hide spinner initially

    // Toggle password visibility (with null check)
    if (togglePassword) {
        togglePassword.addEventListener("click", function () {
            passwordInput.type = passwordInput.type === "password" ? "text" : "password";
            togglePassword.innerHTML =
                passwordInput.type === "password"
                    ? '<i class="fas fa-eye"></i>'
                    : '<i class="fas fa-eye-slash"></i>';
        });
    } else {
        console.warn("Toggle password element not found.");
    }

    // Ensure only numbers are entered for phone number
    phoneInput.addEventListener("input", function () {
        this.value = this.value.replace(/\D/g, "");
        if (this.value.length > 10) {
            this.value = this.value.slice(0, 10);
        }
    });

    function isValidPhoneNumber(phone) {
        const phoneRegex = /^[6-9]\d{9}$/; // Must be 10 digits, starting with 6-9
        return phoneRegex.test(phone);
    }

    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    function checkPasswordStrength(password) {
        let strength = 0;
        if (password.length >= 8) strength++;              // At least 8 characters
        if (/[A-Z]/.test(password)) strength++;             // Contains uppercase letter
        if (/[a-z]/.test(password)) strength++;             // Contains lowercase letter
        if (/\d/.test(password)) strength++;                // Contains a digit
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++; // Contains a special character
        return strength;
    }
    
    function isStrongPassword(password) {
        return checkPasswordStrength(password) === 5;
    }

    // Validate phone number on blur
    phoneInput.addEventListener("blur", function () {
        if (this.value.length > 0 && !isValidPhoneNumber(this.value)) {
            errorMessage.innerText = "Invalid phone number! Must be 10 digits and start with 6-9.";
            errorMessage.style.display = "block";
        } else {
            errorMessage.style.display = "none";
        }
    });

    signupButton.addEventListener("click", async (event) => {
        event.preventDefault();

        const companyName = companyNameInput.value.trim();
        const shopAddress = shopAddressInput.value.trim();
        const pincode = pincodeInput.value.trim();
        const phone = phoneInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();
        const companyLogoFile = companyLogoInput.files[0];

        errorMessage.style.display = "none";
        errorMessage.innerText = "";

        // Check that all required fields are filled in
        if (!companyName || !shopAddress || !pincode || !phone || !email || !password || !confirmPassword) {
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

        if (!isValidPhoneNumber(phone)) {
            errorMessage.innerText = "Invalid phone number! Must be 10 digits and start with 6-9.";
            errorMessage.style.display = "block";
            return;
        }

        signupButton.disabled = true;
        signupButton.querySelector(".button-text").innerText = "Signing up...";
        if (spinner) spinner.style.display = "inline-block";

        try {
            // Check if the email is already registered for an admin account via Django endpoint
            const checkResponse = await fetch('/check-email/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                },
                body: JSON.stringify({ email })
            });
            const checkResult = await checkResponse.json();
            if (!checkResult.success) {
                errorMessage.innerText = checkResult.error;
                errorMessage.style.display = "block";
                return;
            }

            // Create the user in Firebase
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            const user = userCredential.user;
            console.log("✅ Firebase signup successful:", user.uid);

            // Send email verification
            await sendEmailVerification(user);
            console.log("📧 Verification email sent!");

            successMessage.innerText = "Verification email sent! Please verify before logging in.";
            successMessage.style.display = "block";

            // Wait for email verification
            const checkVerification = async () => {
                while (!user.emailVerified) {
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    await user.reload();
                }
                console.log("✅ Email verified! Proceeding with backend registration...");

                // Prepare the form data for backend registration
                let formData = new FormData();
                formData.append("uid", user.uid);
                formData.append("company_name", companyName);
                formData.append("shop_address", shopAddress);
                formData.append("pincode", pincode);
                formData.append("phone", phone);
                formData.append("email", email);
                if (companyLogoFile) {
                    formData.append("company_logo", companyLogoFile);
                }

                // Send the admin registration details to your Django backend
                const backendResponse = await fetch('/admin-signup/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                    },
                });
                const backendResult = await backendResponse.json();
                if (backendResult.success) {
                    successMessage.innerText = "Account verified and created successfully! Redirecting...";
                    setTimeout(() => window.location.href = "/store-admin/dashboard", 1500);
                } else {
                    errorMessage.innerText = backendResult.error;
                    errorMessage.style.display = "block";
                }
            };

            // Listen for auth state changes to trigger the verification check
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
