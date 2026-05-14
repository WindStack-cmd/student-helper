// Dashboard functionality

// Pagination state
let currentPage = 1;
const limit = 20;
let totalRequests = 0;
let searchQuery = "";
let currentTab = "Network Feed";
let performanceChartInstance = null;
let pendingWeeklyActivity = null;
// Global currentUser populated from JWT in localStorage.token (email, first_name etc.)
let currentUser = null;

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

            const categorySelect = document.getElementById("categoryFilter");
            if (categorySelect && categorySelect.value) {
                fetchUrl += `&category=${encodeURIComponent(categorySelect.value)}`;
            }
        } else if (url.includes("get_requests")) {
            let params = new URLSearchParams();
            if (searchQuery) params.append("search", searchQuery);
            const categorySelect = document.getElementById("categoryFilter");
            if (categorySelect && categorySelect.value) params.append("category", categorySelect.value);
            const qs = params.toString();
            if (qs) fetchUrl = `${url}${separator}${qs}`;
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
            let subtitle = emptyText || "No data available.";
            if (currentTab === "Network Feed") {
                subtitle = "No active requests in the network yet. Be the first to post one.";
            } else if (currentTab === "My Data") {
                subtitle = "You haven't posted any requests yet. Post your first question to get started.";
            } else if (currentTab === "Archived") {
                subtitle = "No archived requests yet. Accepted or expired requests will appear here.";
            }
            container.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="ghost" style="width: 42px; height: 42px; color: var(--text-tertiary); opacity: 0.85;"></i>
                    <p class="empty-state-title">NO_DATA_FOUND</p>
                    <p class="empty-state-subtitle">${subtitle}</p>
                </div>
            `;
            renderPaginationControls(false); // Hide pagination if no data
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        data.forEach(req => {
            const badge = renderBadge(req);
            const categoryTag = req.category ? `<span class="status-badge" style="background: rgba(123, 66, 250, 0.1); color: var(--accent-purple); border: 1px solid rgba(123, 66, 250, 0.3);">${req.category}</span>` : '';
            const posterName = req.poster_name || req.first_name || req.name || (req.email ? req.email.split("@")[0] : "ANONYMOUS_USER");

            // Ensure currentUser is initialized from JWT so we can compare by user_id
            if (!currentUser) {
                try {
                    const rawToken = localStorage.getItem('token') || localStorage.getItem('access_token');
                    if (rawToken) {
                        const payloadPart = (rawToken.split('.')[1] || '');
                        const base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
                        const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
                        currentUser = JSON.parse(atob(padded));
                    }
                } catch (e) {
                    console.warn('Failed to decode token for card owner check', e);
                }
            }

            // Ownership check: compare numeric user_id from token with request.user_id
            const isOwnerCard = currentUser && req.user_id && (Number(currentUser.user_id) === Number(req.user_id));
            console.log('Card ownership check:', currentUser && currentUser.user_id, req.user_id, isOwnerCard);

            // Feature 1 & 2: Bounty and Expiry Badges
            let bountyBadge = '';
            if (req.escrowed_bounty > 0) {
                bountyBadge = `<span class="status-badge" style="background: rgba(204, 255, 0, 0.1); color: var(--accent-lime); border: 1px solid var(--accent-lime);"><i data-lucide="lock" style="width:10px; height:10px; margin-right:4px;"></i>${req.escrowed_bounty} LOCKED</span>`;
            } else if (req.solved && req.bounty > 0) {
                bountyBadge = `<span class="status-badge" style="background: rgba(0, 229, 255, 0.1); color: var(--accent-blue); border: 1px solid var(--accent-blue);"><i data-lucide="check" style="width:10px; height:10px; margin-right:4px;"></i>${req.bounty} AWARDED</span>`;
            }

            let expiryInfo = '';
            if (req.status === 'expired') {
                expiryInfo = `<span class="status-badge" style="background: rgba(255, 51, 102, 0.1); color: var(--danger-red); border: 1px solid var(--danger-red);">EXPIRED</span>`;
            } else if (req.expires_at) {
                const expires = new Date(req.expires_at);
                const now = new Date();
                const diffMs = expires - now;
                const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

                if (diffMs <= 0) {
                    expiryInfo = `<span class="status-badge" style="background: rgba(255, 51, 102, 0.1); color: var(--danger-red); border: 1px solid var(--danger-red);">EXPIRED</span>`;
                } else if (diffHours < 24) {
                    expiryInfo = `<span class="status-badge" style="background: rgba(255, 165, 0, 0.1); color: #ffa500; border: 1px solid #ffa500;"><i data-lucide="clock" style="width:10px; height:10px; margin-right:4px;"></i>EXPIRING SOON</span>`;
                } else {
                    const dateStr = expires.toLocaleDateString('en-GB'); // DD/MM/YYYY
                    expiryInfo = `<span class="expiry-date">EXPIRES: ${dateStr}</span>`;
                }
            }

            // Build delete button HTML to sit inline next to the badge on the right
            const deleteBtnHtml = (isOwnerCard && req.status === 'open')
                ? `<button id="cardDeleteBtn-${req.id}" class="btn-outline btn-small" style="color: var(--danger-red); border-color: rgba(255,51,102,0.15); background: transparent; margin-left:8px;">✕ DELETE</button>`
                : '';

            container.innerHTML += `
<div class="data-row" onclick="openRequest(${req.id})" id="requestCard-${req.id}">
    <div class="row-main">
        <div class="row-icon"><i data-lucide="help-circle"></i></div>
        <div>
            <div class="row-title">${req.title}</div>
            <div class="row-meta">${categoryTag}${bountyBadge}${expiryInfo}</div>
            <div class="row-desc">Posted by ${posterName}</div>
        </div>
    </div>
    <div class="row-status-col">${badge}${deleteBtnHtml}</div>
    <div class="row-date">${new Date(req.created_at).toLocaleDateString() || 'NEW_REQUEST'}</div>
</div>`;

            // Attach click handler to the delete button to stop propagation and perform DELETE
            if (isOwnerCard && req.status === 'open') {
                // Use a small timeout to ensure element is in DOM
                setTimeout(() => {
                    const delBtn = document.getElementById(`cardDeleteBtn-${req.id}`);
                    if (!delBtn) return;
                    delBtn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        if (!confirm('Delete this request?')) return;
                        const headers = getAuthHeaders();
                        if (!headers) return showNotification('Not authenticated', 'error');
                        try {
                            const resp = await fetch(`${API_BASE}/requests/${req.id}`, { method: 'DELETE', headers });
                            if (resp.status === 401) {
                                showNotification('Unauthorized', 'error');
                                return;
                            }
                            if (!resp.ok) {
                                const text = await resp.text();
                                showNotification('Failed to delete request', 'error');
                                console.error('Delete failed', resp.status, text);
                                return;
                            }
                            // Remove card from DOM
                            const card = document.getElementById(`requestCard-${req.id}`);
                            if (card) card.remove();
                            showNotification('Request deleted', 'success');
                        } catch (err) {
                            console.error('Delete error', err);
                            showNotification('Error deleting request', 'error');
                        }
                    });
                }, 50);
            }
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
    searchWrapper.className = "filters-row";

    searchWrapper.innerHTML = `
        <div class="category-select-wrap">
            <select id="categoryFilter" class="category-select" onchange="currentPage=1; loadRequests();">
                <option value="">ALL CATEGORIES</option>
                <option value="Math">Math</option>
                <option value="Code">Code</option>
                <option value="Essay">Essay</option>
                <option value="Science">Science</option>
                <option value="Other">Other</option>
            </select>
        </div>
            <div class="search-wrap">
                <i data-lucide="search"></i>
                <input type="text" id="requestSearch" placeholder="SEARCH_DATABASE..." 
                    class="request-search-input">
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
    await fetchAndRenderRequests(API_BASE + "/get_requests", "NO_ACTIVE_REQUESTS",
        (req) => req.status === 'solved' || req.solved
            ? `<span class="status-badge" style="background: rgba(46, 204, 113, 0.1); color: var(--success-green); border: 1px solid var(--success-green);">SOLVED</span>`
            : `<span class="status-badge status-active">LIVE</span>`, true);
}

async function loadMyRequests() {
    currentTab = "My Data";
    // For now, only Network Feed is paginated on backend, but we prepare the logic
    await fetchAndRenderRequests(API_BASE + "/get_my_requests", "NO DATA FOUND",
        (req) => req.status === 'solved' || req.solved
            ? `<span class="status-badge" style="background: rgba(46, 204, 113, 0.1); color: var(--success-green); border: 1px solid var(--success-green);">SOLVED</span>`
            : `<span class="status-badge status-active">LIVE</span>`, false);
}

async function loadArchivedRequests() {
    currentTab = "Archived";
    await fetchAndRenderRequests(API_BASE + "/get_archived_requests", "NO ARCHIVED DATA",
        (req) => req.solved
            ? `<span class="status-badge" style="background: rgba(46, 204, 113, 0.1); color: var(--success-green); border: 1px solid var(--success-green);">SOLVED</span>`
            : `<span class="status-badge" style="background: rgba(255, 255, 255, 0.1); color: var(--text-secondary); border: 1px solid var(--border-dim);">CLOSED</span>`, false);
}

async function loadDashboardMetrics() {
    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        // Force fresh data (no cache) and add a timestamp to bypass intermediaries
        const statsUrl = `${API_BASE}/user_stats?_=${Date.now()}`;
        const response = await fetch(statsUrl, { headers, cache: 'no-store' });

        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        if (!response.ok) throw new Error("HTTP " + response.status);
        const data = await response.json();

        const postedEl = document.getElementById("postedCount");
        const solvedEl = document.getElementById("solvedCount");
        const rankEl = document.getElementById("rankCount");
        const referralEarningsEl = document.getElementById("referralEarningsCount");

        const postedCount = Number(data.bounties_posted || 0);
        const solvedCount = Number(data.bounties_completed || 0);
        const hasRankActivity = postedCount > 0 || solvedCount > 0;

        if (postedEl) postedEl.innerText = postedCount;
        if (solvedEl) solvedEl.innerText = solvedCount;
        if (rankEl) rankEl.innerText = hasRankActivity && data.rank ? `#${data.rank}` : "N/A";
        if (referralEarningsEl) referralEarningsEl.innerText = data.referral_earnings || 0;

        const referralNodeLink = document.getElementById("referralNodeLink");
        const referralCopyBtn = document.querySelector(".referral-card button");
        if (referralNodeLink) {
            if (data.referral_code) {
                const origin = window.location.origin;
                const currentPath = window.location.pathname;
                let basePath = currentPath.substring(0, currentPath.lastIndexOf('/'));
                if (!basePath) basePath = '/pages';
                const link = `${origin}${basePath}/register.html?ref=${data.referral_code}`;
                referralNodeLink.innerText = link;
                referralNodeLink.setAttribute('data-link', link);
                if (referralCopyBtn) {
                    referralCopyBtn.disabled = false;
                    referralCopyBtn.style.opacity = '1';
                    referralCopyBtn.style.cursor = 'pointer';
                }
            } else {
                referralNodeLink.innerText = "NOT_AVAILABLE";
                referralNodeLink.removeAttribute('data-link');
                if (referralCopyBtn) {
                    referralCopyBtn.disabled = true;
                    referralCopyBtn.style.opacity = '0.5';
                    referralCopyBtn.style.cursor = 'not-allowed';
                }
            }
        }

        updateIdentityProtocolPanel(data);
        updatePerformanceChart(data.weekly_activity);
    } catch (e) {
        console.error("Dashboard metrics load error:", e);
    }
}

function updateIdentityProtocolPanel(data) {
    const user = JSON.parse(localStorage.getItem("loggedInUser") || "{}");
    const rank = Number(data.rank || 0);
    const posted = Number(data.bounties_posted || 0);
    const completed = Number(data.bounties_completed || 0);
    const reputation = Number(data.reputation || 0);
    const hasRankActivity = posted > 0 || completed > 0;

    const rankLabel = document.getElementById("identityRankLabel");
    const levelBar = document.getElementById("identityLevelBar");
    const tierProgress = document.getElementById("identityTierProgress");
    const initializedValue = document.getElementById("identityInitializedValue");
    const modulesWrap = document.getElementById("identityCoreModules");
    const objectives = document.getElementById("identityObjectives");

    if (rankLabel) {
        rankLabel.textContent = hasRankActivity && rank > 0 ? `#${rank}` : "UNRANKED";
    }

    if (levelBar) {
        // Calculate progress based on reputation or completed bounties
        // Level up every 10 completed bounties after ranking is initialized.
        const level = hasRankActivity ? Math.floor(completed / 10) + 1 : 0;
        const progressInLevel = hasRankActivity ? (completed % 10) * 10 : 0;
        levelBar.style.width = `${progressInLevel}%`;
        
        // Update initialized value to show level too
        if (initializedValue) {
            initializedValue.textContent = hasRankActivity ? `LVL_${level}_NODE` : "UNRANKED_NODE";
        }
    }

    if (tierProgress) {
        if (!hasRankActivity) {
            tierProgress.textContent = "COMPLETE OR POST A BOUNTY TO START RANKING";
        } else {
        const nextTierAt = (Math.floor(completed / 10) + 1) * 10;
        const toNext = nextTierAt - completed;
        tierProgress.textContent = toNext > 0
            ? `${toNext} COMPLETED BOUNTIES TO NEXT LEVEL`
            : "TIER UPGRADE READY";
        }
    }

    if (modulesWrap) {
        const modules = [
            "Protocol_v4",
            completed > 5 ? "Elite_Solver" : (completed > 0 ? "Active_Solver" : "Junior_Solver"),
            reputation > 500 ? "High_Trust" : "Standard"
        ];
        modulesWrap.innerHTML = modules.map((m, idx) => {
            if (idx === 1) {
                return `<span class="sys-tag" style="border-color: var(--accent-lime); color: var(--accent-lime);">${m}</span>`;
            }
            return `<span class="sys-tag">${m}</span>`;
        }).join("");
    }

    if (objectives) {
        const name = user.first_name || user.name || "Node";
        if (posted === 0) {
            objectives.textContent = `${name}, activate your network footprint by posting your first request.`;
        } else if (completed === 0) {
            objectives.textContent = `${name}, system scan shows 0 solved objectives. Target a bounty to earn reputation.`;
        } else {
            objectives.textContent = `${name}, performance optimal. Continue solving high-yield bounties to increase rank.`;
        }
    }
}

function copyReferral() {
    const linkEl = document.getElementById('referralNodeLink');
    if (!linkEl) return;
    const link = linkEl.getAttribute('data-link');
    if (!link) return;
    navigator.clipboard.writeText(link).then(() => {
        showNotification("Referral link copied to clipboard!", "success");
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showNotification("Failed to copy link.", "error");
    });
}

function copyRequestLink(id) {
    const origin = window.location.origin;
    const currentPath = window.location.pathname;
    let basePath = currentPath.substring(0, currentPath.lastIndexOf('/'));
    if (!basePath) basePath = '/pages';
    const link = `${origin}${basePath}/request-details.html?id=${id}`;
    
    navigator.clipboard.writeText(link).then(() => {
        showNotification("Share link copied to clipboard!", "success");
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showNotification("Failed to copy link.", "error");
    });
}

async function loadNotifications() {
    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        const response = await fetch(API_BASE + "/notifications", { headers });

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
        const response = await fetch(`${API_BASE}/get_request_details/${id}`, { headers });
        if (!response.ok) throw new Error("Load failed");

        const data = await response.json();
        const req = data.request;
        const answers = data.answers;
        const posterName = req.poster_name || req.first_name || req.name || (req.user_email ? req.user_email.split("@")[0] : "ANONYMOUS_USER");

        // Fill Request details
        document.getElementById("modalTitle").innerHTML = `
            <span style="display: flex; align-items: center; gap: 12px;">
                REQUEST_ID_${String(req.id).padStart(3, '0')}
                <button onclick="copyRequestLink(${req.id})" class="btn-icon" style="width: 28px; height: 28px; background: rgba(255,255,255,0.05); border: 1px solid var(--border-dim);" title="COPY_SHARE_LINK">
                    <i data-lucide="share-2" style="width: 14px; height: 14px;"></i>
                </button>
            </span>
        `;
        document.getElementById("modalDesc").innerText = req.description;
        document.getElementById("modalAuthor").innerText = posterName;
        document.getElementById("modalDate").innerText = new Date(req.created_at).toLocaleString();
        document.getElementById("modalBounty").innerText = `${req.bounty || 0} PTS`;
        document.getElementById("answerCount").innerText = `(${answers.length})`;

        // Expiry Status in Modal
        const bountyVal = document.getElementById("modalBounty");
        if (req.status === 'expired') {
            bountyVal.innerHTML = `<span style="color: var(--danger-red);">EXPIRED (Bounty Returned)</span>`;
            document.getElementById("modalAnswerInput").disabled = true;
            document.getElementById("modalAnswerInput").placeholder = "This request has EXPIRED and no longer accepts answers.";
            document.getElementById("modalSubmitBtn").disabled = true;
        } else {
            bountyVal.innerText = `${req.bounty || 0} PTS`;
            document.getElementById("modalAnswerInput").disabled = false;
            document.getElementById("modalAnswerInput").placeholder = "Enter your technical solution or guidance here...";
            document.getElementById("modalSubmitBtn").disabled = false;
        }

        // Ensure global currentUser is populated from JWT in localStorage (token) so ownership checks work
        try {
            const token = localStorage.getItem('token') || localStorage.getItem('access_token');
            if (token && !currentUser) {
                const payload = JSON.parse(atob((token.split('.')[1] || '').replace(/-/g, '+').replace(/_/g, '/')));
                currentUser = payload;
            }
        } catch (e) {
            console.error('Token parse error', e);
        }

        console.log('Current user from token:', currentUser);
        console.log('Request posted_by fields:', req.user_email, req.poster_name, req.first_name || req.name);

        // Ownership check: prefer comparing numeric user_id from token against req.user_id
        const isOwner = currentUser && req.user_id && (Number(currentUser.user_id) === Number(req.user_id));
        console.log('Ownership check:', currentUser && currentUser.user_id, req.user_id, isOwner);

        const claimsCount = document.getElementById("claimsCount");
        const claimantsList = document.getElementById("claimantsList");
        const claimBtn = document.getElementById("claimBtn");

        const currentFirstName = currentUser.first_name || currentUser.name || "";

        claimsCount.innerText = data.claims_count || 0;
        claimantsList.innerText = data.claimants && data.claimants.length > 0 ? `WORKING_NOW: ${data.claimants.join(', ')}` : 'NO_ACTIVE_CLAIMS';

        // Fix 2: Hide claim button entirely for owner
        if (isOwner) {
            claimBtn.style.display = 'none';
        } else {
            claimBtn.style.display = 'flex';
            const isClaimedByMe = data.claimants && data.claimants.includes(currentFirstName);

            if (isClaimedByMe) {
                claimBtn.innerHTML = '<i data-lucide="x-circle" style="width: 14px; height: 14px;"></i> DROP_CLAIM';
                claimBtn.style.background = 'var(--danger-red)';
                claimBtn.style.borderColor = 'var(--danger-red)';
                claimBtn.onclick = () => toggleClaim(req.id, true);
            } else {
                claimBtn.innerHTML = '<i data-lucide="target" style="width: 14px; height: 14px;"></i> CLAIM_OBJECTIVE';
                claimBtn.style.background = 'var(--accent-blue)';
                claimBtn.style.borderColor = 'var(--accent-blue)';
                claimBtn.onclick = () => toggleClaim(req.id, false);
            }

            if (req.status !== 'open') {
                claimBtn.disabled = true;
                claimBtn.style.opacity = '0.5';
            } else {
                claimBtn.disabled = false;
                claimBtn.style.opacity = '1';
            }
        }

        // Setup Full Page link
        document.getElementById("modalExternalLink").onclick = () => {
            window.location.href = "request-details.html?id=" + id;
        };

        // Add delete icon button into modal header (top-right) so it's always visible regardless of scroll
        try {
            const header = document.querySelector('#requestModal .modal-header');
            if (header) {
                // Remove existing header delete if present
                const existingHeaderDel = document.getElementById('modalHeaderDeleteBtn');
                if (existingHeaderDel) existingHeaderDel.remove();

                if (isOwner && req.status === 'open') {
                    const headerDel = document.createElement('button');
                    headerDel.id = 'modalHeaderDeleteBtn';
                    headerDel.title = 'DELETE_REQUEST';
                    headerDel.className = 'btn-icon';
                    headerDel.style.color = 'var(--danger-red)';
                    headerDel.style.border = 'none';
                    headerDel.style.background = 'transparent';
                    headerDel.style.marginRight = '8px';
                    headerDel.innerHTML = '<i data-lucide="trash-2" style="width:18px;height:18px;"></i>';
                    headerDel.onclick = (e) => { e.stopPropagation(); if (confirm('Are you sure you want to delete this bounty?')) deleteRequest(req.id); };

                    // Place before the existing close button if present
                    const closeBtn = header.querySelector('button[onclick="closeRequestModal()"]');
                    if (closeBtn && closeBtn.parentNode === header) {
                        header.insertBefore(headerDel, closeBtn);
                    } else {
                        header.appendChild(headerDel);
                    }
                    if (window.lucide) lucide.createIcons();
                }
            }
        } catch (e) {
            console.warn('Failed to insert header delete button', e);
        }

        // Render Answers
        renderModalAnswers(answers, isOwner, req.status, req.id, req.user_email);

        loading.style.display = "none";
        content.style.display = "block";

        // UX SIGNAL: Block owner from seeing answer form (Fix)
        const answerSection = document.querySelector(".answer-section");
        if (answerSection) {
            if (isOwner) {
                answerSection.innerHTML = `
                    <div style="padding: 16px; text-align: center; border: 1px dashed var(--border-dim); border-radius: 8px; opacity: 0.6;">
                        <span style="color: var(--text-tertiary); font-family: var(--font-mono); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">
                           CANNOT_RESPOND: REQUEST_OWNER
                        </span>
                    </div>
                `;
            } else {
                answerSection.style.display = (req.status === 'open' || req.status === 'captured') ? "block" : "none";
            }
        }

        if (window.lucide) lucide.createIcons();
    } catch (error) {
        console.error("Modal load error:", error);
        document.getElementById("modalBody").innerHTML = `<div style="padding:40px; color:var(--danger-red); text-align:center; font-family:var(--font-mono);">ERROR_FETCHING_NODE_DATA</div>`;
    }
}

async function deleteRequest(id) {
    if (!confirm("Are you sure? This will delete the request and return your escrowed bounty.")) return;

    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        const res = await fetch(`${API_BASE}/requests/${id}`, {
            method: "DELETE",
            headers: headers
        });

        if (res.ok) {
            showNotification("Request deleted and bounty returned.", "success");
            closeRequestModal();
            // Refresh current view
            if (currentTab === "Network Feed") await loadRequests();
            else if (currentTab === "My Data") await loadMyRequests();
            else if (currentTab === "Archived") await loadArchivedRequests();
            if (typeof fetchBalance === 'function') fetchBalance();
            // Optimistically update posted count in UI immediately
            try {
                const postedEl = document.getElementById("postedCount");
                if (postedEl) {
                    const current = Number(postedEl.innerText) || 0;
                    const updated = Math.max(0, current - 1);
                    postedEl.innerText = updated;
                }
            } catch (err) { console.warn('Failed to update postedCount optimistically', err); }

            // Then refresh authoritative metrics from server
            try { await loadDashboardMetrics(); } catch (e) { console.error('Failed to refresh dashboard metrics', e); }
        } else {
            const data = await res.json();
            alert(data.message || "Deletion failed.");
        }
    } catch (e) {
        console.error("Delete error:", e);
    }
}

function closeRequestModal() {
    const modal = document.getElementById("requestModal");
    if (modal) modal.style.display = "none";
    currentActiveRequestId = null;
    document.getElementById("modalSubmitBtn").disabled = false;
    document.getElementById("modalSubmitBtn").innerHTML = '<i data-lucide="send" style="width: 14px; height: 14px;"></i> PUSH_ANSWER';
}

function renderModalAnswers(answers, isOwner, requestStatus, requestId, ownerEmail) {
    const container = document.getElementById("modalAnswers");
    if (!container) return;

    if (answers.length === 0) {
        container.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-tertiary); font-family:var(--font-mono); font-size:0.8rem;">NO_RESPONSES_LOGGED_YET</div>`;
        return;
    }

    container.innerHTML = answers.map(ans => {
        let acceptBtn = '';
        // Fix: Do not show accept button if the owner is the one who wrote the answer
        const isSelfAnswer = ans.email === ownerEmail;

        if (isOwner && requestStatus === 'open' && !ans.accepted && !isSelfAnswer) {
            acceptBtn = `
                <button onclick="acceptAnswer(${ans.id}, ${requestId})" class="btn-outline" style="padding: 4px 8px; font-size: 0.7rem; color: var(--accent-lime); border-color: var(--accent-lime); margin-left: 8px;">
                    <i data-lucide="check-circle" style="width: 12px; height: 12px;"></i> ACCEPT_ANSWER
                </button>
            `;
        } else if (ans.accepted) {
            acceptBtn = `<span class="status-badge" style="background: rgba(204, 255, 0, 0.1); color: var(--accent-lime); border: 1px solid var(--accent-lime); margin-left: 8px; font-size: 0.6rem;">ACCEPTED_SOLUTION</span>`;
        }

        return `
            <div class="answer-card" style="position: relative; ${ans.accepted ? 'border-left: 2px solid var(--accent-lime);' : ''}">
                <div class="answer-header">
                    <span class="answer-author">${ans.email}</span>
                    <span class="answer-date">${new Date(ans.created_at).toLocaleDateString()}</span>
                </div>
                <div class="answer-content">${ans.answer}</div>
                <div style="margin-top: 12px; display: flex; align-items: center; gap: 8px;">
                    <button onclick="upvoteAnswer(${ans.id}, this)" class="btn-outline" style="padding: 4px 8px; font-size: 0.7rem; background: var(--bg-base);">
                        <i data-lucide="chevron-up" style="width: 12px; height: 12px;"></i> UPVOTE (${ans.upvotes || 0})
                    </button>
                    ${acceptBtn}
                </div>
            </div>
        `;
    }).join('');
    if (window.lucide) lucide.createIcons();
}

async function acceptAnswer(answerId, requestId) {
    if (!confirm("Are you sure? This will award the bounty and close the request.")) return;

    const headers = getAuthHeaders();
    if (!headers) return;

    try {
        const response = await fetch(API_BASE + "/accept_answer", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({ answer_id: answerId, request_id: requestId })
        });

        if (response.ok) {
            showNotification("Solution accepted! Bounty awarded.", "success");
            openRequest(requestId); // Refresh modal
            // Refresh feed to update status badges
            if (currentTab === "Network Feed") await loadRequests();
            else if (currentTab === "My Data") await loadMyRequests();
            else if (currentTab === "Archived") await loadArchivedRequests();
            // Accepting a solution affects solved counts and rank — refresh dashboard metrics
            try { await loadDashboardMetrics(); } catch (e) { console.error('Failed to refresh dashboard metrics', e); }
        } else {
            const data = await response.json();
            showNotification(data.message || "Failed to accept answer", "error");
        }
    } catch (e) {
        console.error("Accept error:", e);
        showNotification("Network error", "error");
    }
}

async function toggleClaim(requestId, isCurrentlyClaimed) {
    const headers = getAuthHeaders();
    if (!headers) return;

    const url = isCurrentlyClaimed ? API_BASE + "/unclaim_request" : API_BASE + "/claim_request";
    const method = isCurrentlyClaimed ? "DELETE" : "POST";

    try {
        const response = await fetch(url, {
            method: method,
            headers: headers,
            body: JSON.stringify({ request_id: requestId })
        });

        if (response.ok) {
            showNotification(isCurrentlyClaimed ? "Claim dropped" : "Objective claimed!", "success");
            openRequest(requestId); // Refresh modal
            // Claiming/unclaiming may affect node activity—refresh metrics
            try { await loadDashboardMetrics(); } catch (e) { console.error('Failed to refresh dashboard metrics', e); }
        } else {
            const err = await response.json();
            showNotification(err.message || "Action failed", "error");
        }
    } catch (e) {
        console.error("Claim toggle error:", e);
    }
}

async function upvoteAnswer(answerId, btnElement) {
    const originalText = btnElement.innerHTML;
    btnElement.innerHTML = "Voting...";
    btnElement.disabled = true;

    try {
        const response = await fetch(API_BASE + "/upvote_answer", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ answer_id: answerId })
        });

        if (!response.ok) throw new Error("Failed to upvote");

        // Refresh modal to see new data
        openRequest(currentActiveRequestId);
    } catch (e) {
        console.error(e);
        alert("Failed to upvote");
        btnElement.innerHTML = originalText;
        btnElement.disabled = false;
    }
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
        const response = await fetch(API_BASE + "/post_answer", {
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
        const dataResponse = await fetch(`${API_BASE}/get_request_details/${id}`, {
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
window.addEventListener("load", function () {
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
    const ctx = document.getElementById("performanceChart");
    if (!ctx) return;

    const initialData = Array.isArray(pendingWeeklyActivity) && pendingWeeklyActivity.length === 7
        ? pendingWeeklyActivity
        : [0, 0, 0, 0, 0, 0, 0];

    // SaaS Level Visualization
    performanceChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'],
            datasets: [{
                label: 'NODE_EFFICIENCY',
                data: initialData,
                backgroundColor: 'rgba(204, 255, 0, 0.2)',
                borderColor: '#ccff00',
                borderWidth: 1,
                borderRadius: 2,
                hoverBackgroundColor: '#ccff00',
                hoverBorderColor: '#ccff00'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0a0a0e',
                    titleFont: { family: 'JetBrains Mono' },
                    bodyFont: { family: 'JetBrains Mono' },
                    borderColor: 'rgba(204, 255, 0, 0.3)',
                    borderWidth: 1
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.03)' },
                    ticks: { display: false }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#4a4a5e', font: { family: 'JetBrains Mono', size: 9 } }
                }
            }
        }
    });
}

function updatePerformanceChart(weeklyActivity) {
    const safeData = Array.isArray(weeklyActivity) && weeklyActivity.length === 7
        ? weeklyActivity.map(v => {
            const n = Number(v);
            return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0;
        })
        : [0, 0, 0, 0, 0, 0, 0];

    pendingWeeklyActivity = safeData;

    if (!performanceChartInstance) {
        return;
    }

    performanceChartInstance.data.datasets[0].data = safeData;
    performanceChartInstance.update();
}

document.addEventListener("click", function (e) {
    if (!e.target.closest(".user-profile-nav")) {
        const dropdown = document.getElementById("profileDropdown");
        if (dropdown) dropdown.classList.remove("show");
    }

    // Close modal if clicking overlay
    if (e.target.classList.contains("modal-overlay")) {
        closeRequestModal();
        closeCommandPalette();
    }
});

// ----- COMMAND PALETTE LOGIC -----
const commands = [
    { name: "Create New Request", icon: "plus", action: () => window.location.href = "request-help.html", shortcut: "N" },
    { name: "View Leaderboard", icon: "bar-chart-2", action: () => window.location.href = "leaderboard.html", shortcut: "L" },
    { name: "Switch to Network Feed", icon: "cpu", action: () => document.querySelector(".tab")?.click(), shortcut: "1" },
    { name: "View My Data", icon: "folder-open", action: () => document.querySelectorAll(".tab")[1]?.click(), shortcut: "2" },
    { name: "View Archive", icon: "archive", action: () => document.querySelectorAll(".tab")[2]?.click(), shortcut: "3" },
    { name: "Check Notifications", icon: "bell", action: () => loadNotifications(), shortcut: "B" },
    { name: "Operational Settings", icon: "sliders", action: () => window.location.href = "settings.html", shortcut: "S" },
    { name: "Logout Protocol", icon: "power", action: () => logoutUser(), shortcut: "X" }
];

let selectedCommandIndex = 0;

function openCommandPalette() {
    const palette = document.getElementById("commandPalette");
    const input = document.getElementById("commandInput");
    if (!palette || !input) return;

    palette.style.display = "flex";
    input.value = "";
    input.focus();
    renderCommands("");
}

function closeCommandPalette() {
    const palette = document.getElementById("commandPalette");
    if (palette) palette.style.display = "none";
}

function renderCommands(filter) {
    const container = document.getElementById("commandResults");
    if (!container) return;

    const filtered = commands.filter(c => c.name.toLowerCase().includes(filter.toLowerCase()));

    container.innerHTML = filtered.map((c, i) => `
        <div class="command-item ${i === selectedCommandIndex ? 'selected' : ''}" onclick="executeCommand(${commands.indexOf(c)})">
            <i data-lucide="${c.icon}" style="width: 14px; height: 14px;"></i>
            <span>${c.name}</span>
            <span class="command-shortcut">${c.shortcut}</span>
        </div>
    `).join("");

    if (window.lucide) lucide.createIcons();
}

function executeCommand(index) {
    if (commands[index]) {
        commands[index].action();
        closeCommandPalette();
    }
}

// Global Keyboard Shortcuts
document.addEventListener("keydown", (e) => {
    // Ctrl+K to open
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        openCommandPalette();
    }

    const palette = document.getElementById("commandPalette");
    if (palette && palette.style.display === "flex") {
        if (e.key === "Escape") {
            closeCommandPalette();
        } else if (e.key === "ArrowDown") {
            e.preventDefault();
            selectedCommandIndex = (selectedCommandIndex + 1) % commands.length;
            renderCommands(document.getElementById("commandInput").value);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            selectedCommandIndex = (selectedCommandIndex - 1 + commands.length) % commands.length;
            renderCommands(document.getElementById("commandInput").value);
        } else if (e.key === "Enter") {
            e.preventDefault();
            const filter = document.getElementById("commandInput").value;
            const filtered = commands.filter(c => c.name.toLowerCase().includes(filter.toLowerCase()));
            if (filtered[selectedCommandIndex]) {
                filtered[selectedCommandIndex].action();
                closeCommandPalette();
            }
        }
    }
});

const cmdInput = document.getElementById("commandInput");
if (cmdInput) {
    cmdInput.addEventListener("input", (e) => {
        selectedCommandIndex = 0;
        renderCommands(e.target.value);
    });
}
