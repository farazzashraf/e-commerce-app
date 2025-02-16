import { initializeApp } from 'firebase/app';

// Ensure Firebase SDK is loaded before initializing
if (typeof firebase === "undefined") {
    console.error("❌ Firebase SDK is not loaded before firebase-config.js!");
} else {
    // Firebase project configuration
    const firebaseConfig = {
        apiKey: "AIzaSyAkHqN2udZ4XZB6Wyir3I3_EMKkLYT5khc",
        authDomain: "thrift-shop-a1808.firebaseapp.com",
        projectId: "thrift-shop-a1808",
        storageBucket: "thrift-shop-a1808.firebasestorage.app",
        messagingSenderId: "82249712532",
        appId: "1:82249712532:web:eb27d4c3591b156ab64581",
        measurementId: "G-PK06Y5WW3M"
    };

    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);

}