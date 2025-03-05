document.addEventListener("DOMContentLoaded", function () {
    document.body.addEventListener("click", function () {
        fetch("/check-login-status/")
            .then(response => response.json())
            .then(data => {
                if (!data.is_logged_in) {
                    showLoginNotification();
                }
            })
            .catch(error => console.error("Error checking login status:", error));
    });
});

function showLoginNotification() {
    if (document.getElementById("login-notification")) return; // Prevent duplicates

    let notification = document.createElement("div");
    notification.id = "login-notification";

    notification.innerHTML = `
        <p>You need to log in!</p>
        <a href="/login/" class="login-btn">Login</a>
    `;

    // Styling
    Object.assign(notification.style, {
        position: "fixed",
        top: "20px",
        left: "50%",
        transform: "translateX(-50%)",
        background: "#fff",
        color: "#333",
        padding: "15px 25px",
        borderRadius: "10px",
        boxShadow: "0 4px 10px rgba(0, 0, 0, 0.2)",
        fontSize: "16px",
        fontWeight: "bold",
        zIndex: "1000",
        display: "flex",
        alignItems: "center",
        gap: "15px",
        border: "2px solid #ff5555",
        transition: "opacity 0.5s ease-in-out"
    });

    let loginBtn = notification.querySelector(".login-btn");
    Object.assign(loginBtn.style, {
        background: "#ff5555",
        color: "#fff",
        textDecoration: "none",
        padding: "6px 12px",
        borderRadius: "5px",
        fontSize: "14px",
        fontWeight: "bold",
        cursor: "pointer"
    });

    document.body.appendChild(notification);

    // Remove after 2 seconds with fade-out effect
    setTimeout(() => {
        notification.style.opacity = "0";
        setTimeout(() => notification.remove(), 500);
    }, 2000);
}
