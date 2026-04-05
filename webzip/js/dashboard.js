// Dashboard functionality

async function fetchAndRenderRequests(url, emptyText, renderBadge) {
    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        const response = await fetch(url, { headers });
        
        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        if (!response.ok) throw new Error("Fetch failed");
        const data = await response.json();
        const container = document.getElementById("requestsContainer");
        if (!container) return;
        container.innerHTML = "";

        if (!data || data.length === 0) {
            container.innerHTML = `<div style="padding:30px;font-family:var(--font-mono);color:var(--text-secondary); text-align: center;">${emptyText}</div>`;
            return;
        }

        data.forEach(req => {
            const badge = renderBadge(req);
            container.innerHTML += `
<div class="data-row" onclick="openRequest(${req.id})">
    <div class="row-main">
        <div class="row-icon"><i data-lucide="help-circle"></i></div>
        <div>
            <div class="row-title">${req.title}</div>
            <div class="row-desc">Posted by ${req.email}</div>
        </div>
    </div>
    <div class="row-status-col">${badge}</div>
    <div class="row-date">NEW_REQUEST</div>
</div>`;
        });
        if (typeof lucide !== "undefined" && lucide.createIcons) {
            lucide.createIcons();
        }
    } catch (error) {
        const container = document.getElementById("requestsContainer");
        if (container) container.innerHTML = `<div style="padding:30px;font-family:var(--font-mono);color:var(--danger-red); text-align: center;">ERROR_LOADING_NETWORK_FEED</div>`;
    }
}

async function loadRequests() {
    await fetchAndRenderRequests("http://127.0.0.1:5000/get_requests", "NO_ACTIVE_REQUESTS",
        () => `<span class="status-badge status-active">LIVE</span>`);
}

async function loadMyRequests() {
    // Backend now gets identity from JWT token
    await fetchAndRenderRequests("http://127.0.0.1:5000/get_my_requests", "NO DATA FOUND",
        () => `<span class="status-badge status-active">LIVE</span>`);
}

async function loadArchivedRequests() {
    await fetchAndRenderRequests("http://127.0.0.1:5000/get_archived_requests", "NO ARCHIVED DATA",
        (req) => req.solved
            ? `<span class="status-badge" style="background: rgba(46, 204, 113, 0.1); color: var(--success-green); border: 1px solid var(--success-green);">SOLVED</span>`
            : `<span class="status-badge" style="background: rgba(255, 255, 255, 0.1); color: var(--text-secondary); border: 1px solid var(--border-dim);">CLOSED</span>`);
}

async function loadDashboardMetrics() {
    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        const response = await fetch("http://127.0.0.1:5000/dashboard_metrics", { headers });
        
        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        if (!response.ok) throw new Error("HTTP " + response.status);
        const data = await response.json();

        const solvedEl = document.getElementById("solvedCount");
        const pointsEl = document.getElementById("pointsCount");
        const pendingEl = document.getElementById("pendingCount");

        if (solvedEl) solvedEl.innerText = data.bounties_cleared;
        if (pointsEl) pointsEl.innerText = data.ledger_stake;
        if (pendingEl) pendingEl.innerText = data.pending_jobs;
    } catch (e) {
        console.error("Dashboard metrics load error:", e);
    }
}

async function loadNotifications() {
    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        const response = await fetch("http://127.0.0.1:5000/notifications", { headers });

        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        const data = await response.json();
        const container = document.getElementById("notificationContainer");
        if (!container) return;

        container.innerHTML = "";

        if (data.length === 0) {
            container.innerHTML = `<div style="font-family:var(--font-mono);color:var(--text-secondary);padding:10px;">NO_NEW_NOTIFICATIONS</div>`;
            return;
        }

        data.forEach(n => {
            container.innerHTML += `<div style="padding:10px; border-bottom:1px solid #333; font-family:var(--font-mono);">🔔 ${n.message}</div>`;
        });
    } catch (error) {
        const container = document.getElementById("notificationContainer");
        if (container) container.innerHTML = `<div style="color:red;padding:10px;">ERROR_LOADING_NOTIFICATIONS</div>`;
    }
}

function openRequest(id) {
    window.location.href = "request-details.html?id=" + id;
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

// Initialize Dashboard
window.addEventListener("load", function() {
    const userStr = localStorage.getItem("loggedInUser");
    if (!userStr) {
        window.location.href = "login.html";
        return;
    }
    const user = JSON.parse(userStr);
    const username = user.first_name || user.name || (user.email ? user.email.split('@')[0] : "User");
    
    if (document.querySelector(".user-profile-nav")) {
        document.querySelector(".user-profile-nav span").textContent = username.charAt(0).toUpperCase();
    }
    
    // Load dynamic data
    loadDashboardMetrics();
    loadRequests();
    
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
