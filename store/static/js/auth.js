document.addEventListener("DOMContentLoaded", function () {
    if (typeof firebase === "undefined") {
        console.error("🔥 Firebase SDK is not loaded!");
        return;
    }

    console.log("✅ Firebase SDK is loaded!");

    const auth = firebase.auth();
    console.log(auth);  // Check if the auth object is available

    // Handle Login
    document.getElementById("loginForm")?.addEventListener("submit", function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        // Validate input fields
        if (!email || !password) {
            console.error("❌ Please fill in both email and password");
            document.getElementById("errorMessage").innerText = "Please fill in both email and password.";
            return;
        }

        auth.signInWithEmailAndPassword(email, password)
            .then((userCredential) => {
                console.log("✅ User signed in:", userCredential.user);
                window.location.href = "/"; // Redirect to homepage
            })
            .catch((error) => {
                console.error("❌ Login error:", error.message);
                document.getElementById("errorMessage").innerText = error.message;
            });
    });
});
