// Dashboard functionality

// Pagination state
let currentPage = 1;
const limit = 20;
let totalRequests = 0;
let searchQuery = "";
let currentTab = "Network Feed";

async function fetchAndRenderRequests(url, emptyText, renderBadge, isPaginated = false) {
    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        // Build URL with pagination and search if needed
        let fetchUrl = url;
        const separator = url.includes('?') ? '&' : '?';

        if (isPaginated) {
            const offset = (currentPage - 1) * limit;
            fetchUrl = `${url}${separator}limit=${limit}&offset=${offset}`;
            if (searchQuery) {
                fetchUrl += `&search=${encodeURIComponent(searchQuery)}`;
            }
        } else if (searchQuery && url.includes("get_requests")) {
            // Apply search even to non-paginated if it's the right endpoint
            fetchUrl = `${url}${separator}search=${encodeURIComponent(searchQuery)}`;
        }

        const response = await fetch(fetchUrl, { headers });

        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        if (response.status === 429) {
            showNotification("Rate limit exceeded. Please try again later.", "error");
            console.error("Rate limited (429)");
            return;
        }

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const result = await response.json();
        const container = document.getElementById("requestsContainer");
        if (!container) return;
        container.innerHTML = "";

        // Handle both paginated and non-paginated responses
        const data = isPaginated ? (result.data || []) : (Array.isArray(result) ? result : []);
        totalRequests = isPaginated ? (result.total || 0) : data.length;

        if (!data || data.length === 0) {
            container.innerHTML = `<div style="padding:30px;font-family:var(--font-mono);color:var(--text-secondary); text-align: center;">${emptyText}</div>`;
            renderPaginationControls(false); // Hide pagination if no data
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
    <div class="row-date">${new Date(req.created_at).toLocaleDateString() || 'NEW_REQUEST'}</div>
</div>`;
        });

        if (isPaginated) {
            renderPaginationControls(true);
        } else {
            renderPaginationControls(false);
        }

        if (typeof lucide !== "undefined" && lucide.createIcons) {
            lucide.createIcons();
        }
    } catch (error) {
        console.error("Fetch error:", error);
        const container = document.getElementById("requestsContainer");
        if (container) container.innerHTML = `<div style="padding:30px;font-family:var(--font-mono);color:var(--danger-red); text-align: center;">ERROR_LOADING_DATA</div>`;
        renderPaginationControls(false);
    }
}

function renderPaginationControls(visible) {
    let paginationDiv = document.getElementById("paginationContainer");
    
    // Create Search UI if it doesn't exist
    renderSearchUI();

    // Create container if it doesn't exist
    if (!paginationDiv) {
        const workspacePanel = document.querySelector(".workspace-panel");
        if (!workspacePanel) return;
        
        paginationDiv = document.createElement("div");
        paginationDiv.id = "paginationContainer";
        paginationDiv.style = "display: flex; justify-content: center; align-items: center; gap: 15px; padding: 20px; border-top: 1px solid var(--border-dim); background: rgba(10, 10, 14, 0.4);";
        workspacePanel.appendChild(paginationDiv);
    }

    if (!visible) {
        paginationDiv.style.display = "none";
        return;
    }

    paginationDiv.style.display = "flex";
    const totalPages = Math.ceil(totalRequests / limit) || 1;

    paginationDiv.innerHTML = `
        <button id="prevPage" class="btn-icon" ${currentPage === 1 ? 'disabled style="opacity: 0.3; cursor: not-allowed;"' : ''}>
            <i data-lucide="chevron-left"></i>
        </button>
        <span style="font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-primary); text-transform: uppercase;">
            Page ${currentPage} of ${totalPages}
        </span>
        <button id="nextPage" class="btn-icon" ${currentPage * limit >= totalRequests ? 'disabled style="opacity: 0.3; cursor: not-allowed;"' : ''}>
            <i data-lucide="chevron-right"></i>
        </button>
    `;

    document.getElementById("prevPage").onclick = () => changePage(currentPage - 1);
    document.getElementById("nextPage").onclick = () => changePage(currentPage + 1);

    if (typeof lucide !== "undefined" && lucide.createIcons) {
        lucide.createIcons();
    }
}

async function changePage(newPage) {
    if (newPage < 1 || (newPage - 1) * limit >= totalRequests) return;
    
    currentPage = newPage;
    // Scroll to top of list
    const panel = document.querySelector(".workspace-panel");
    if (panel) panel.scrollTop = 0;
    
    // Show loading state
    const container = document.getElementById("requestsContainer");
    if (container) container.innerHTML = `<div style="padding:30px;font-family:var(--font-mono);color:var(--text-secondary); text-align: center;">REFRESHING_FEED...</div>`;

    if (currentTab === "Network Feed") {
        await loadRequests();
    } else if (currentTab === "My Data") {
        await loadMyRequests();
    } else if (currentTab === "Archived") {
        await loadArchivedRequests();
    }
}

let searchTimeout;
function renderSearchUI() {
    const tabsContainer = document.querySelector(".panel-tabs");
    if (!tabsContainer || document.getElementById("searchWrapper")) return;

    // Create wrapper for the right side of tabs
    const searchWrapper = document.createElement("div");
    searchWrapper.id = "searchWrapper";
    searchWrapper.style = "margin-left: auto; display: flex; align-items: center; padding-right: 24px; pointer-events: auto;";

    searchWrapper.innerHTML = `
        <div style="position: relative; display: flex; align-items: center;">
            <i data-lucide="search" style="position: absolute; left: 12px; width: 14px; height: 14px; color: var(--text-tertiary);"></i>
            <input type="text" id="requestSearch" placeholder="SEARCH_DATABASE..." 
                style="background: var(--bg-surface); border: 1px solid var(--border-dim); border-radius: 6px; padding: 8px 12px 8px 36px; color: var(--text-primary); font-family: var(--font-mono); font-size: 0.75rem; width: 220px; transition: all 0.2s; outline: none;"
                onfocus="this.style.borderColor='var(--text-secondary)'"
                onblur="this.style.borderColor='var(--border-dim)'">
        </div>
    `;

    tabsContainer.appendChild(searchWrapper);

    const searchInput = document.getElementById("requestSearch");
    searchInput.addEventListener("input", (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(async () => {
            searchQuery = e.target.value.trim();
            currentPage = 1; // RESET_PAGINATION
            
            // Re-load current tab with search
            if (currentTab === "Network Feed") {
                await loadRequests();
            } else if (currentTab === "My Data") {
                await loadMyRequests();
            } else if (currentTab === "Archived") {
                await loadArchivedRequests();
            }
        }, 400); // DEBOUNCE_DELAY
    });

    if (window.lucide) lucide.createIcons();
}

async function loadRequests() {
    currentTab = "Network Feed";
    await fetchAndRenderRequests("http://127.0.0.1:5001/get_requests", "NO_ACTIVE_REQUESTS",
        () => `<span class="status-badge status-active">LIVE</span>`, true);
}

async function loadMyRequests() {
    currentTab = "My Data";
    // For now, only Network Feed is paginated on backend, but we prepare the logic
    await fetchAndRenderRequests("http://127.0.0.1:5001/get_my_requests", "NO DATA FOUND",
        () => `<span class="status-badge status-active">LIVE</span>`, false);
}

async function loadArchivedRequests() {
    currentTab = "Archived";
    await fetchAndRenderRequests("http://127.0.0.1:5001/get_archived_requests", "NO ARCHIVED DATA",
        (req) => req.solved
            ? `<span class="status-badge" style="background: rgba(46, 204, 113, 0.1); color: var(--success-green); border: 1px solid var(--success-green);">SOLVED</span>`
            : `<span class="status-badge" style="background: rgba(255, 255, 255, 0.1); color: var(--text-secondary); border: 1px solid var(--border-dim);">CLOSED</span>`, false);
}

async function loadDashboardMetrics() {
    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        const response = await fetch("http://127.0.0.1:5001/dashboard_metrics", { headers });
        
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
        const response = await fetch("http://127.0.0.1:5001/notifications", { headers });

        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const container = document.getElementById("notificationContainer");
        if (!container) return;

        container.innerHTML = "";

        if (!data || data.length === 0) {
            container.innerHTML = `<div style="font-family:var(--font-mono);color:var(--text-secondary);padding:10px;">NO_NEW_NOTIFICATIONS</div>`;
            return;
        }

        data.forEach(n => {
            container.innerHTML += `<div style="padding:10px; border-bottom:1px solid #333; font-family:var(--font-mono);">🔔 ${n.message}</div>`;
        });
    } catch (error) {
        console.error("Notification load error:", error);
        const container = document.getElementById("notificationContainer");
        if (container) container.innerHTML = `<div style="color:red;padding:10px;">ERROR_LOADING_NOTIFICATIONS</div>`;
    }
}

let currentActiveRequestId = null;

async function openRequest(id) {
    const modal = document.getElementById("requestModal");
    const loading = document.getElementById("modalLoading");
    const content = document.getElementById("modalContent");
    
    if (!modal) return;
    
    currentActiveRequestId = id;
    modal.style.display = "flex";
    loading.style.display = "flex";
    content.style.display = "none";

    const headers = getAuthHeaders();
    try {
        const response = await fetch(`http://127.0.0.1:5001/get_request_details/${id}`, { headers });
        if (!response.ok) throw new Error("Load failed");
        
        const data = await response.json();
        const req = data.request;
        const answers = data.answers;

        // Fill Request details
        document.getElementById("modalTitle").innerText = `REQUEST_ID_${String(req.id).padStart(3, '0')}`;
        document.getElementById("modalDesc").innerText = req.description;
        document.getElementById("modalAuthor").innerText = req.user_email || "ANONYMOUS_USER";
        document.getElementById("modalDate").innerText = new Date(req.created_at).toLocaleString();
        document.getElementById("modalBounty").innerText = `${req.bounty || 0} PTS`;
        document.getElementById("answerCount").innerText = `(${answers.length})`;
        
        // Setup Full Page link
        document.getElementById("modalExternalLink").onclick = () => {
            window.location.href = "request-details.html?id=" + id;
        };

        // Render Answers
        renderModalAnswers(answers);

        loading.style.display = "none";
        content.style.display = "block";
        
        if (window.lucide) lucide.createIcons();
    } catch (error) {
        console.error("Modal load error:", error);
        document.getElementById("modalBody").innerHTML = `<div style="padding:40px; color:var(--danger-red); text-align:center; font-family:var(--font-mono);">ERROR_FETCHING_NODE_DATA</div>`;
    }
}

function closeRequestModal() {
    const modal = document.getElementById("requestModal");
    if (modal) modal.style.display = "none";
    currentActiveRequestId = null;
    document.getElementById("modalSubmitBtn").disabled = false;
    document.getElementById("modalSubmitBtn").innerHTML = '<i data-lucide="send" style="width: 14px; height: 14px;"></i> PUSH_ANSWER';
}

function renderModalAnswers(answers) {
    const container = document.getElementById("modalAnswers");
    if (!container) return;
    
    if (answers.length === 0) {
        container.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-tertiary); font-family:var(--font-mono); font-size:0.8rem;">NO_RESPONSES_LOGGED_YET</div>`;
        return;
    }
    
    container.innerHTML = answers.map(ans => `
        <div class="answer-card">
            <div class="answer-header">
                <span class="answer-author">${ans.email}</span>
                <span class="answer-date">${new Date(ans.created_at).toLocaleDateString()}</span>
            </div>
            <div class="answer-content">${ans.answer}</div>
        </div>
    `).join('');
}

async function submitModalAnswer() {
    const input = document.getElementById("modalAnswerInput");
    const btn = document.getElementById("modalSubmitBtn");
    const id = currentActiveRequestId;

    if (!input || !input.value.trim() || !id) {
        alert("MISSING_FIELDS");
        return;
    }

    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerText = "UPLOADING...";

    const userStr = localStorage.getItem("loggedInUser");
    if (!userStr) {
        alert("NOT_LOGGED_IN");
        btn.disabled = false;
        btn.innerHTML = originalText;
        return;
    }

    const user = JSON.parse(userStr);
    const email = user.email;

    // Debug: Check values
    console.log("Submitting answer:", { request_id: id, answer: input.value.trim(), email: email });

    try {
        const response = await fetch("http://127.0.0.1:5001/post_answer", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify({
                request_id: id,
                answer: input.value.trim(),
                email: email
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.message || errorData.error || (`HTTP ${response.status}`);
            console.error("Backend error:", errorData);
            alert(`ERROR: ${errorMsg}`);
            btn.disabled = false;
            btn.innerHTML = originalText;
            return;
        }

        // Refresh answers
        const dataResponse = await fetch(`http://127.0.0.1:5001/get_request_details/${id}`, {
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("access_token")}`
            }
        });
        const refreshedData = await dataResponse.json();

        renderModalAnswers(refreshedData.answers);
        document.getElementById("answerCount").innerText = `(${refreshedData.answers.length})`;

        input.value = "";
        btn.disabled = false;
        btn.innerHTML = originalText;

        if (window.lucide) lucide.createIcons();
    } catch (e) {
        console.error("Submit error:", e);
        alert(`NETWORK_ERROR: ${e.message}`);
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
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

function logoutUser() {
    if (typeof logout === "function") {
        logout();
    } else {
        localStorage.removeItem("access_token");
        localStorage.removeItem("loggedInUser");
        window.location.href = "login.html";
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
    
    // Update identity display
    const userNameEls = document.querySelectorAll("#userName");
    const userAvatarEls = document.querySelectorAll("#userAvatar");
    const userEmailEls = document.querySelectorAll("#userEmail");

    userNameEls.forEach(el => el.innerText = username);
    userAvatarEls.forEach(el => el.innerText = username.charAt(0).toUpperCase());
    userEmailEls.forEach(el => el.innerText = user.email || "");
    
    // Load dynamic data
    loadDashboardMetrics();
    loadRequests();
    
    // Setup Tab listeners
    const tabs = document.querySelectorAll(".panel-tabs .tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", async () => {
            if (tab.classList.contains("active")) return;

            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            
            currentPage = 1; // Reset pagination
            const tabText = tab.textContent.trim();
            
            if (tabText === "Network Feed") {
                await loadRequests();
            } else if (tabText === "My Data") {
                await loadMyRequests();
            } else if (tabText === "Archived") {
                await loadArchivedRequests();
            }
        });
    });

    // Initialize chart
    initializeChart();
    
    // Add animation to stat cards
    animateStatCards();
    
    // Create icons
    if (window.lucide) lucide.createIcons();
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
    
    // Close modal if clicking overlay
    if (e.target.classList.contains("modal-overlay")) {
        closeRequestModal();
    }
});
