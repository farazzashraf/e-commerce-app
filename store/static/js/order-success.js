document.addEventListener("DOMContentLoaded", () => {
    const confettiSettings = { 
        particleCount: 250, 
        spread: 100, 
        origin: { y: 0.6 },
        colors: ['#34D399', '#10B981', '#059669']  // Green shades
    };
    confetti(confettiSettings);
});