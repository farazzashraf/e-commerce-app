// Import Firebase modules
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-app.js";
import { getAuth, GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-auth.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-analytics.js";

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyAc3PJiGzPKpNDhZmuneE6Dcx8C5cd-hPQ",
    authDomain: "ecommerce-307ec.firebaseapp.com",
    projectId: "ecommerce-307ec",
    storageBucket: "ecommerce-307ec.appspot.com",
    // storageBucket: "ecommerce-307ec.firebasestorage.app",
    messagingSenderId: "500663795876",
    appId: "1:500663795876:web:4b2288690d988e74362631",
    measurementId: "G-1TPH0K5V3B"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Export Firebase Auth so other files can use it
export { auth, googleProvider };
