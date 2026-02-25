// ===== UTILITY FUNCTIONS FOR ALL PAGES =====

// Show notification toast
function showNotification(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `notification-toast notification-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${type === 'success' ? '#2ecc71' : type === 'error' ? '#ff4d4d' : '#007bff'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 10000;
        animation: slideInUp 0.3s ease;
        font-weight: bold;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ===== AUTHENTICATION FUNCTIONS =====

// Auth API object for handling authentication
const authAPI = {
    async login(email, password) {
        return new Promise((resolve) => {
            setTimeout(() => {
                if (!email || !password) {
                    resolve({ error: 'Please fill all fields!' });
                    return;
                }

                // Check if user exists
                let users = JSON.parse(localStorage.getItem("users")) || [];
                let user = users.find(u => u.email === email && u.password === password);

                if (!user) {
                    // Allow demo login for any email/password combination
                    if (email && password) {
                        user = {
                            email: email,
                            name: email.split('@')[0],
                            id: Date.now()
                        };
                        // Save demo user
                        users.push({...user, password: password});
                        localStorage.setItem("users", JSON.stringify(users));
                    } else {
                        resolve({ error: 'Invalid email or password!' });
                        return;
                    }
                }

                // Store logged in user
                localStorage.setItem("loggedInUser", JSON.stringify(user));
                localStorage.setItem("currentUser", JSON.stringify(user));

                resolve({ user: user });
            }, 500); // Simulate API delay
        });
    },

    async register(email, password, confirmPassword, name) {
        return new Promise((resolve) => {
            setTimeout(() => {
                if (!email || !password || !confirmPassword || !name) {
                    resolve({ error: 'Please fill all fields!' });
                    return;
                }

                if (password !== confirmPassword) {
                    resolve({ error: 'Passwords do not match!' });
                    return;
                }

                if (password.length < 6) {
                    resolve({ error: 'Password must be at least 6 characters!' });
                    return;
                }

                // Check if user already exists
                let users = JSON.parse(localStorage.getItem("users")) || [];
                if (users.find(u => u.email === email)) {
                    resolve({ error: 'Email already registered!' });
                    return;
                }

                // Create new user
                const newUser = {
                    email: email,
                    password: password,
                    name: name,
                    id: Date.now(),
                    created: new Date().toISOString()
                };

                users.push(newUser);
                localStorage.setItem("users", JSON.stringify(users));

                // Auto login after registration
                localStorage.setItem("loggedInUser", JSON.stringify(newUser));
                localStorage.setItem("currentUser", JSON.stringify(newUser));

                resolve({ user: newUser });
            }, 500); // Simulate API delay
        });
    },

    async logout() {
        return new Promise((resolve) => {
            setTimeout(() => {
                localStorage.removeItem("loggedInUser");
                localStorage.removeItem("currentUser");
                resolve();
            }, 200);
        });
    }
};

function validateForm() {
    var email = document.getElementById("registerEmail")?.value || "";
    var password = document.getElementById("password")?.value || "";
    var confirmPassword = document.getElementById("confirmPassword")?.value || "";
    var error = document.getElementById("error");

    if (!email || !password || !confirmPassword) {
        if (error) error.textContent = "Please fill all fields!";
        return false;
    }

    if (password !== confirmPassword) {
        if (error) error.textContent = "Passwords do not match!";
        return false;
    }

    if (password.length < 6) {
        if (error) error.textContent = "Password must be at least 6 characters!";
        return false;
    }

    // Save user to localStorage
    const newUser = {
        email: email,
        password: password,
        name: email.split('@')[0],
        created: new Date().toISOString()
    };
    
    let users = JSON.parse(localStorage.getItem("users")) || [];
    users.push(newUser);
    localStorage.setItem("users", JSON.stringify(users));

    if (error) error.textContent = "Registration successful! Redirecting to login...";
    if (error) error.style.color = "green";
    
    setTimeout(function() {
        window.location.href = "login.html";
    }, 2000);
    
    return false;
}

function loginValidate() {
    var email = document.getElementById("loginEmail")?.value || "";
    var password = document.getElementById("loginPassword")?.value || "";
    var error = document.getElementById("loginError");

    if (!email || !password) {
        if (error) error.textContent = "Please fill all fields!";
        return false;
    }

    // Check if user exists (simplified - in real app would use backend)
    let users = JSON.parse(localStorage.getItem("users")) || [];
    let user = users.find(u => u.email === email && u.password === password);
    
    if (!user) {
        // Allow demo login
        if (email && password) {
            user = { email: email, name: email.split('@')[0] };
        } else {
            if (error) error.textContent = "Invalid email or password!";
            return false;
        }
    }

    localStorage.setItem("loggedInUser", JSON.stringify(user));
    showNotification("Login successful! Welcome " + user.name, "success");
    
    setTimeout(() => window.location.href = "dashboard.html", 500);
    return false;
}

function logout() {
    // Call backend logout API
    authAPI.logout().then(() => {
        localStorage.removeItem("loggedInUser");
        localStorage.removeItem("currentUser");
        showNotification("You have been logged out", "info");
        setTimeout(() => window.location.href = "index.html", 500);
    }).catch(error => {
        console.error('Logout error:', error);
        // Still logout locally even if API fails
        localStorage.removeItem("loggedInUser");
        localStorage.removeItem("currentUser");
        setTimeout(() => window.location.href = "index.html", 500);
    });
}

function checkAuthentication() {
    const loggedInUser = localStorage.getItem("loggedInUser");
    if (!loggedInUser) {
        showNotification("Please login first!", "error");
        setTimeout(() => window.location.href = "login.html", 500);
        return false;
    }
    return true;
}

// ===== NAVIGATION FUNCTIONS =====

function goToDashboard() {
    window.location.href = "dashboard.html";
}

function goToCommunity() {
    window.location.href = "community-chat.html";
}

function goToLeaderboard() {
    window.location.href = "leaderboard.html";
}

function goToProfile() {
    window.location.href = "user-profile.html";
}

function goToSettings() {
    window.location.href = "settings.html";
}

function goToNotifications() {
    window.location.href = "notifications.html";
}

function goToHome() {
    window.location.href = "index.html";
}

function goToAbout() {
    window.location.href = "about.html";
}

function goToContact() {
    window.location.href = "contact.html";
}

// ===== HELP REQUEST FUNCTIONS =====

function submitHelpRequest(event) {
    if (event) event.preventDefault();

    const title = document.getElementById("requestTitle")?.value;
    const type = document.getElementById("helpType")?.value;
    const description = document.getElementById("requestDesc")?.value;

    if (!title || !type || !description) {
        showNotification("Please fill all fields!", "error");
        return false;
    }

    let requests = JSON.parse(localStorage.getItem("helpRequests")) || [];
    const newRequest = {
        id: Date.now(),
        title: title,
        type: type,
        description: description,
        status: "Pending",
        date: new Date().toLocaleDateString(),
        timestamp: new Date()
    };

    requests.push(newRequest);
    localStorage.setItem("helpRequests", JSON.stringify(requests));

    showNotification("Help request submitted successfully!", "success");
    setTimeout(() => window.location.href = "dashboard.html", 1500);
    return false;
}

function viewRequest(index) {
    localStorage.setItem("selectedRequestIndex", index);
    showNotification("Loading request details...", "info");
    setTimeout(() => window.location.href = "help-request.html", 300);
}

function acceptRequest(index) {
    let requests = JSON.parse(localStorage.getItem("helpRequests")) || [];
    if (requests[index]) {
        requests[index].status = "Accepted";
        localStorage.setItem("helpRequests", JSON.stringify(requests));
        showNotification("Request accepted! User will be notified.", "success");
        setTimeout(() => location.reload(), 800);
    }
}

function acceptHelp() {
    showNotification("Help accepted! Thank you for helping!", "success");
    setTimeout(() => window.location.href = "dashboard.html", 1500);
}

// ===== PROFILE FUNCTIONS =====

function editProfile() {
    const modal = document.getElementById("editProfileModal");
    if (modal) modal.style.display = "block";
}

function closeEditProfile() {
    const modal = document.getElementById("editProfileModal");
    if (modal) modal.style.display = "none";
}

function saveProfile(event) {
    if (event) event.preventDefault();
    
    const name = document.getElementById("profileName")?.value;
    const bio = document.getElementById("profileBio")?.value;
    
    if (!name) {
        showNotification("Please enter your name!", "error");
        return false;
    }

    const user = JSON.parse(localStorage.getItem("loggedInUser")) || {};
    user.name = name;
    user.bio = bio;
    
    localStorage.setItem("loggedInUser", JSON.stringify(user));
    showNotification("Profile updated successfully!", "success");
    closeEditProfile();
    setTimeout(() => location.reload(), 800);
    return false;
}

function viewProfile() {
    window.location.href = "user-profile.html";
}

// ===== NOTIFICATION FUNCTIONS =====

function markAllAsRead() {
    const notifications = document.querySelectorAll(".notification-card.unread");
    notifications.forEach(n => n.classList.remove("unread"));
    showNotification("All notifications marked as read", "success");
}

function clearAllNotifications() {
    const container = document.querySelector(".notification-list");
    if (container) {
        container.innerHTML = '<p style="text-align: center; color: #999;">No notifications</p>';
    }
    showNotification("All notifications cleared", "info");
}

// ===== DROPDOWN MENU =====

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        const dropBtn = document.getElementById("dropbtn");
        const dropdown = document.getElementById("dropdown-menu");

        if (dropBtn) {
            dropBtn.addEventListener("click", function (e) {
                e.stopPropagation();
                dropdown?.classList.toggle("show");
            });

            window.addEventListener("click", function () {
                dropdown?.classList.remove("show");
            });
        }
    });
} else {
    const dropBtn = document.getElementById("dropbtn");
    const dropdown = document.getElementById("dropdown-menu");

    if (dropBtn) {
        dropBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            dropdown?.classList.toggle("show");
        });

        window.addEventListener("click", function () {
            dropdown?.classList.remove("show");
        });
    }
}

// ===== ADVANCED PROFILE DROPDOWN =====

function initAdvancedProfileDropdown() {
    const profileBtn = document.getElementById("profileBtn");
    const profileDropdown = document.getElementById("advancedProfileDropdown");
    const profileDropdownMenu = document.getElementById("profileDropdownMenu");
    const profileAvatar = document.getElementById("profileAvatar");
    const dropdownAvatar = document.querySelector(".dropdown-avatar");
    const dropdownUsername = document.getElementById("dropdownUsername");
    
    // Only initialize if on a page with the dropdown
    if (!profileDropdown) return;
    
    // Get user data
    const user = JSON.parse(localStorage.getItem("loggedInUser")) || {};
    const username = user.email ? user.email.split('@')[0] : "User";
    const userInitial = username.charAt(0).toUpperCase();
    
    // Update avatar and username
    if (profileAvatar) profileAvatar.textContent = userInitial;
    if (dropdownAvatar) dropdownAvatar.textContent = userInitial;
    if (dropdownUsername) dropdownUsername.textContent = username;
    
    // Toggle dropdown on button click
    if (profileBtn) {
        profileBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            profileDropdown.classList.toggle("active");
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener("click", function(e) {
        if (!profileDropdown.contains(e.target)) {
            profileDropdown.classList.remove("active");
        }
    });
    
    // Close dropdown when clicking on a menu item
    if (profileDropdownMenu) {
        const dropdownItems = profileDropdownMenu.querySelectorAll(".dropdown-item");
        dropdownItems.forEach(item => {
            item.addEventListener("click", function() {
                profileDropdown.classList.remove("active");
            });
        });
    }
}

// ===== THEME TOGGLE =====

function toggleDarkMode() {
    const isDark = localStorage.getItem("darkMode") === "true";
    localStorage.setItem("darkMode", !isDark);
    location.reload();
}

// ===== INITIALIZATION =====

window.addEventListener("load", function() {
    // Update navbar with user info if logged in
    const user = JSON.parse(localStorage.getItem("loggedInUser"));
    if (user && document.querySelector(".user-profile-nav")) {
        const firstLetter = user.name?.charAt(0).toUpperCase() || user.email?.charAt(0).toUpperCase();
        const elements = document.querySelectorAll("[id*='userAvatar']");
        elements.forEach(el => el.textContent = firstLetter);
    }
    
    // Initialize advanced profile dropdown if it exists
    initAdvancedProfileDropdown();
});

// ===== COMMUNITY PAGE FUNCTIONS =====

function performSearch() {
    const query = document.getElementById('searchInputNav')?.value;
    if (query) {
        showNotification(`Searching for: ${query}`, "info");
        // Implement search functionality
    }
}

function toggleTheme() {
    const isDark = localStorage.getItem("darkMode") === "true";
    localStorage.setItem("darkMode", !isDark);
    document.body.classList.toggle("dark-mode", !isDark);
    showNotification(`Switched to ${!isDark ? 'dark' : 'light'} mode`, "info");
}

function toggleNotificationCenter() {
    const center = document.getElementById('notificationCenter');
    if (center) {
        center.classList.toggle('show');
    }
}

function closeNotificationCenter() {
    const center = document.getElementById('notificationCenter');
    if (center) {
        center.classList.remove('show');
    }
}

function viewProfile() {
    window.location.href = "user-profile.html";
}

function viewMyQuestions() {
    showNotification("My Questions feature coming soon!", "info");
}

function viewBookmarks() {
    showNotification("Bookmarks feature coming soon!", "info");
}

function viewAchievements() {
    showNotification("Achievements feature coming soon!", "info");
}

function openSettings() {
    window.location.href = "settings.html";
}

function filterByCategory(category, event) {
    // Remove active class from all categories
    document.querySelectorAll('.category-item-advanced').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to clicked category
    event.currentTarget.classList.add('active');
    
    showNotification(`Filtered by: ${category}`, "info");
}

function changeSort() {
    const sortBy = document.getElementById('sortBy')?.value;
    showNotification(`Sorted by: ${sortBy}`, "info");
}

function toggleFilter(filter) {
    showNotification(`Toggled filter: ${filter}`, "info");
}

function switchTab(tab, event) {
    // Remove active class from all tabs
    document.querySelectorAll('.tab-btn-advanced').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to clicked tab
    event.currentTarget.classList.add('active');
    
    showNotification(`Switched to ${tab} tab`, "info");
}

function openAskModal() {
    showNotification("Ask Question modal coming soon!", "info");
}

