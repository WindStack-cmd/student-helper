// Profile page functionality

async function loadProfile() {
    const userStr = localStorage.getItem("loggedInUser");
    if (!userStr) {
        window.location.href = "login.html";
        return;
    }

    try {
        const user = JSON.parse(userStr);
        const name = user.first_name || user.name || (user.email ? user.email.split("@")[0] : "User");
        const email = user.email || "";

        // Main profile elements
        const nameEl = document.getElementById("profileName");
        const emailEl = document.getElementById("profileEmail");
        const nameInput = document.getElementById("profileNameInput");
        const emailInput = document.getElementById("profileEmailInput");
        const mainAvatar = document.getElementById("mainAvatar");
        const sidebarName = document.getElementById("sidebarName");
        const sidebarAvatar = document.getElementById("sidebarAvatar");
        const sidebarEmail = document.getElementById("sidebarEmail");

        if (nameEl) nameEl.innerText = name;
        if (emailEl) emailEl.innerText = email;
        if (nameInput) nameInput.value = name;
        if (emailInput) emailInput.value = email;
        if (mainAvatar) mainAvatar.innerText = name.charAt(0).toUpperCase();

        // Update sidebar elements
        if (sidebarName) sidebarName.innerText = name;
        if (sidebarAvatar) sidebarAvatar.innerText = name.charAt(0).toUpperCase();
        if (sidebarEmail) sidebarEmail.innerText = email;

        // Fetch user stats securely
        await loadUserStats();

    } catch (e) {
        console.error("Profile parsing error:", e);
    }
}

async function loadUserStats() {
    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        // Backend now handles identity via JWT
        const response = await fetch("http://127.0.0.1:5000/user_stats", { headers });
        
        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        if (!response.ok) throw new Error("HTTP " + response.status);
        const stats = await response.json();

        const statVals = document.querySelectorAll(".spotlight-stats .val");
        if (statVals.length >= 2) {
            statVals[0].textContent = stats.reputation !== undefined ? stats.reputation : 0;
            statVals[1].textContent = stats.bounties_completed !== undefined ? stats.bounties_completed : 0;
        }
    } catch (err) {
        console.error("Failed to load user stats", err);
    }
}

function saveProfile(event) {
    if (event) event.preventDefault();
    
    const name = document.getElementById("profileNameInput")?.value;
    const bio = document.querySelector("textarea")?.value;
    
    // In real app, this would be an API call
    showNotification("Profile updated successfully! ✅", "success");
    
    // Update local state temporarily
    const userStr = localStorage.getItem("loggedInUser");
    if (userStr) {
        const user = JSON.parse(userStr);
        user.first_name = name;
        localStorage.setItem("loggedInUser", JSON.stringify(user));
    }
    
    loadProfile();
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

// Initialize profile page
window.addEventListener("load", function() {
    loadProfile();
});

document.addEventListener("click", function(e) {
    if (!e.target.closest(".user-profile-nav")) {
        const dropdown = document.getElementById("profileDropdown");
        if (dropdown) dropdown.classList.remove("show");
    }
});
