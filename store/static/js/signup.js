document.getElementById("signupForm").addEventListener("submit", function (event) {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    if (password !== confirmPassword) {
        document.getElementById("errorMessage").textContent = "Passwords do not match!";
        return;
    }

    firebase.auth().createUserWithEmailAndPassword(email, password)
        .then((userCredential) => {
            return userCredential.user.getIdToken();
        })
        .then((idToken) => {
            return fetch("/login-redirect/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": idToken
                },
                body: JSON.stringify({ token: idToken })
            });
        })
        .then(response => response.json())
        .then(data => {
            window.location.href = data.redirect_url || "/";
        })
        .catch((error) => {
            document.getElementById("errorMessage").textContent = error.message;
        });
});
