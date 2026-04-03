// Profile page functionality

function toggleProfileMenu() {
    const dropdown = document.getElementById("profileDropdown");
    if (dropdown) {
        dropdown.classList.toggle("show");
    }
}

function editProfile() {
    document.getElementById("editProfileModal").style.display = "flex";
}

function closeEditProfile(event) {
    if (event && event.target.id !== "editProfileModal") return;
    document.getElementById("editProfileModal").style.display = "none";
}

function saveProfile(event) {
    if (event) event.preventDefault();
    showNotification("Profile updated successfully! ✅", "success");
    closeEditProfile();
}

function switchProfileTab(tab, event) {
    // Hide all tabs
    document.getElementById("activityTab").style.display = "none";
    document.getElementById("questionsTab").style.display = "none";
    document.getElementById("answersTab").style.display = "none";
    document.getElementById("savedTab").style.display = "none";
    
    // Remove active class from buttons
    document.querySelectorAll(".profile-tab-btn").forEach(btn => {
        btn.classList.remove("active");
    });
    
    // Show selected tab
    const tabMap = {
        "activity": "activityTab",
        "questions": "questionsTab",
        "answers": "answersTab",
        "saved": "savedTab"
    };
    
    if (tabMap[tab]) {
        const targetTab = document.getElementById(tabMap[tab]);
        if (targetTab) targetTab.style.display = "block";
        if (event && event.target) {
            event.target.classList.add("active");
        }
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
    const user = JSON.parse(localStorage.getItem("loggedInUser")) || {};
    const username = user.email ? user.email.split('@')[0] : "User";

    const profileUserName = document.getElementById("profileUserName");
    const profileUserEmail = document.getElementById("profileUserEmail");
    const userAvatarNav = document.getElementById("userAvatarNav");
    if (profileUserName) profileUserName.textContent = username;
    if (profileUserEmail) profileUserEmail.textContent = user.email || "user@example.com";
    if (userAvatarNav) userAvatarNav.textContent = username.charAt(0).toUpperCase();
    
    // Set random banner color
    const colors = ["#667eea", "#764ba2", "#f093fb", "#4facfe"];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    const profileBanner = document.getElementById("profileBanner");
    if (profileBanner) {
        profileBanner.style.background = `linear-gradient(135deg, ${randomColor}, ${colors[1]})`;
    }
});

document.addEventListener("click", function(e) {
    if (!e.target.closest(".user-profile-nav")) {
        const dropdown = document.getElementById("profileDropdown");
        if (dropdown) dropdown.classList.remove("show");
    }
});
