document.getElementById("loginForm").addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent default form submission

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    firebase.auth().signInWithEmailAndPassword(email, password)
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
            if (data.redirect_url) {
                window.location.href = data.redirect_url; // Redirect to last page visited
            } else {
                window.location.href = "/";
            }
        })
        .catch((error) => {
            document.getElementById("errorMessage").textContent = error.message;
        });
});
