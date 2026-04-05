// Leaderboard functionality

async function loadLeaderboard() {
    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        const response = await fetch("http://127.0.0.1:5000/leaderboard", { headers });
        
        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        const tbody = document.querySelector(".log-table tbody") || document.getElementById("leaderboardBody");

        if (!response.ok) {
            if (tbody) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; opacity:0.5;">SCAN MORE NODES...</td></tr>';
            return;
        }

        const users = await response.json();

        if (!tbody) return;
        if (!users || users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; opacity:0.5;">SCAN MORE NODES...</td></tr>';
        } else {
            tbody.innerHTML = users.map((user, index) => {
                let rankStr = String(index + 1).padStart(2, '0');
                let initials = (user.first_name || "U").substring(0, 2).toUpperCase();
                return `
                    <tr class="ranking-row">
                        <td class="row-rank">${rankStr}</td>
                        <td class="row-user">
                            <div class="row-avatar">${initials}</div>
                            <div class="row-name">${user.first_name || "User"}</div>
                        </td>
                        <td class="row-rep">${user.reputation} <span>REP</span></td>
                        <td>${user.bounties_completed || 0}</td>
                    </tr>
                `;
            }).join('');
        }

        // Update My Rank Badge
        const localUserRaw = localStorage.getItem("loggedInUser");
        if (localUserRaw) {
            const localUser = JSON.parse(localUserRaw);
            const rankIndex = users.findIndex(u => u.email === localUser.email);
            const rankBadge = document.querySelector(".my-rank");
            if (rankBadge) {
                rankBadge.textContent = rankIndex >= 0 ? "#" + (rankIndex + 1) : "Unranked";
            }
        }
    } catch (e) {
        console.error("Leaderboard error:", e);
        const tbody = document.querySelector(".log-table tbody") || document.getElementById("leaderboardBody");
        if (tbody) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; opacity:0.5;">SCAN MORE NODES...</td></tr>';
    }
}

function filterLeaderboard(filter, event) {
    // Update active filter button
    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.classList.remove("active");
    });
    if (event && event.target) {
        event.target.classList.add("active");
    }
    
    // In real app, would fetch from backend with filters
    showNotification(`Filtering ledger by ${filter}...`, "info");
    loadLeaderboard(); 
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

// Initialize leaderboard
window.addEventListener("load", function() {
    loadLeaderboard();
    
    const userStr = localStorage.getItem("loggedInUser");
    if (userStr) {
        const user = JSON.parse(userStr);
        const username = user.first_name || user.name || (user.email ? user.email.split('@')[0] : "User");
        
        if (document.getElementById("userAvatarNav")) {
            document.getElementById("userAvatarNav").textContent = username.charAt(0).toUpperCase();
        }

        // Shared sidebar profile loader logic can also go here or in sidebar.js
        if (typeof loadUserProfile === 'function') loadUserProfile();
    }
});

document.addEventListener("click", function(e) {
    if (!e.target.closest(".user-profile-nav")) {
        const dropdown = document.getElementById("profileDropdown");
        if (dropdown) dropdown.classList.remove("show");
    }
});
