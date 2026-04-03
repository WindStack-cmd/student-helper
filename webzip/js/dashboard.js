// Dashboard functionality

function goToCommunity() {
    window.location.href = "community-chat.html";
}

function toggleProfileMenu() {
    const dropdown = document.getElementById("profileDropdown");
    if (dropdown) {
        dropdown.classList.toggle("show");
    }
}

function logout() {
    localStorage.removeItem("loggedInUser");
    window.location.href = "index.html";
}

function showNotification(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `notification-toast show ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize Dashboard
window.addEventListener("load", function() {
    const user = JSON.parse(localStorage.getItem("loggedInUser")) || {};
    const username = user.email ? user.email.split('@')[0] : "User";
    
    if (document.querySelector(".user-profile-nav")) {
        document.querySelector(".user-profile-nav span").textContent = username.charAt(0).toUpperCase();
    }
    
    // Initialize chart
    initializeChart();
    
    // Add animation to stat cards
    animateStatCards();
});

function animateStatCards() {
    const cards = document.querySelectorAll(".stat-card");
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.animation = "slideInUp 0.5s ease";
        }, index * 100);
    });
}

function initializeChart() {
    const canvas = document.getElementById("performanceChart");
    if (!canvas) return;
    
    // Simple chart representation
    const ctx = canvas.getContext("2d");
    const width = canvas.width = canvas.offsetWidth;
    const height = canvas.height = 200;
    
    ctx.fillStyle = "#667eea";
    ctx.fillRect(0, height - 40, width / 7, 40);
    ctx.fillRect(width / 6, height - 50, width / 7, 50);
    ctx.fillRect(width / 3, height - 60, width / 7, 60);
    ctx.fillRect(width / 2 - 10, height - 70, width / 7, 70);
    ctx.fillRect(width * 2 / 3 - 10, height - 80, width / 7, 80);
    ctx.fillRect(width * 5 / 6 - 15, height - 90, width / 7, 90);
}

document.addEventListener("click", function(e) {
    if (!e.target.closest(".user-profile-nav")) {
        const dropdown = document.getElementById("profileDropdown");
        if (dropdown) dropdown.classList.remove("show");
    }
});

