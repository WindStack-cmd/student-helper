// Leaderboard functionality

const leaderboardData = [
    { rank: 1, name: "John Doe", reputation: 3250, answers: 128, upvotes: 234, badges: "🥇🎖️⭐" },
    { rank: 2, name: "Sarah Johnson", reputation: 2450, answers: 89, upvotes: 156, badges: "🥈🎖️" },
    { rank: 3, name: "Emma Wilson", reputation: 2120, answers: 76, upvotes: 145, badges: "🥉" },
    { rank: 4, name: "Mike Chen", reputation: 1890, answers: 64, upvotes: 120, badges: "🎖️" },
    { rank: 5, name: "Priya Singh", reputation: 1750, answers: 58, upvotes: 98, badges: "" },
    { rank: 6, name: "Alex Kumar", reputation: 1620, answers: 52, upvotes: 87, badges: "" },
    { rank: 7, name: "Lisa Anderson", reputation: 1480, answers: 47, upvotes: 75, badges: "" },
    { rank: 8, name: "David Lee", reputation: 1350, answers: 43, upvotes: 68, badges: "" },
    { rank: 9, name: "Rachel Brown", reputation: 1220, answers: 39, upvotes: 56, badges: "" },
    { rank: 10, name: "Tom Wilson", reputation: 1090, answers: 35, upvotes: 48, badges: "" }
];

function loadLeaderboard() {
    const tbody = document.getElementById("leaderboardBody");
    if (!tbody) return;
    tbody.innerHTML = leaderboardData.map(user => `
        <tr>
            <td class="rank-cell">
                <span class="rank-badge">#${user.rank}</span>
            </td>
            <td>
                <div class="user-cell">
                    <span class="user-avatar-small">${user.name.charAt(0)}</span>
                    <span class="user-name">${user.name}</span>
                </div>
            </td>
            <td><strong>${user.reputation}</strong></td>
            <td>${user.answers}</td>
            <td>${user.upvotes}</td>
            <td>${user.badges}</td>
            <td><button class="view-profile-btn" onclick="viewProfile('${user.name}')">View</button></td>
        </tr>
    `).join('');
}

function filterLeaderboard(filter, event) {
    // Update active filter button
    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.classList.remove("active");
    });
    if (event && event.target) {
        event.target.classList.add("active");
    }
    
    // Simulate filtering (in real app, would fetch from backend)
    const notification = `Leaderboard filtered by: ${filter.replace('-', ' ').toUpperCase()}`;
    showNotification(notification, "info");
}

function viewProfile(userName) {
    showNotification(`Opening profile for ${userName}...`, "info");
    // In real app, would navigate to user profile
}

function goToCommunity() {
    window.location.href = "community-chat.html";
}

function toggleProfileMenu() {
    const dropdown = document.getElementById("profileDropdown");
    if (dropdown) {
        dropdown.classList.toggle("show");
    }
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

function logout() {
    localStorage.removeItem("loggedInUser");
    window.location.href = "index.html";
}

// Initialize leaderboard
window.addEventListener("load", function() {
    loadLeaderboard();
    
    const user = JSON.parse(localStorage.getItem("loggedInUser")) || {};
    const username = user.email ? user.email.split('@')[0] : "User";
    
    if (document.getElementById("userAvatarNav")) {
        document.getElementById("userAvatarNav").textContent = username.charAt(0).toUpperCase();
    }
});

document.addEventListener("click", function(e) {
    if (!e.target.closest(".user-profile-nav")) {
        const dropdown = document.getElementById("profileDropdown");
        if (dropdown) dropdown.classList.remove("show");
    }
});
