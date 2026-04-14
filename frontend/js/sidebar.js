// ========================================
// SIDEBAR.JS — Reusable Navigation Component
// Injects the sidebar HTML into any page
// ========================================

/**
 * Renders the sidebar navigation into a container element.
 * 
 * @param {Object} options
 * @param {string} options.activePage - The key of the currently active page
 * @param {string} options.context - 'app' for logged-in pages, 'public' for public pages (about, contact)
 * @param {string} [options.containerId='sidebar-root'] - ID of the container element
 */
function renderSidebar(options = {}) {
    const {
        activePage = '',
        context = 'app',
        containerId = 'sidebar-root'
    } = options;

    const container = document.getElementById(containerId);
    if (!container) return;

    // Get user data from localStorage
    const user = JSON.parse(localStorage.getItem('loggedInUser')) || {};
    const userName = user.first_name || user.name || user.email?.split('@')[0] || 'Guest User';
    const userEmail = user.email || '';
    const userInitials = userName.charAt(0).toUpperCase();
    const isLoggedIn = !!user.email;

    // Determine base path (are we in /pages/ or root?)
    const inPages = window.location.pathname.includes('/pages/');
    const rootPrefix = inPages ? '../' : '';
    const pagesPrefix = inPages ? '' : 'pages/';

    let sidebarHTML = '';

    if (context === 'public') {
        sidebarHTML = buildPublicSidebar({ activePage, rootPrefix, pagesPrefix, userName, userInitials, isLoggedIn });
    } else {
        sidebarHTML = buildAppSidebar({ activePage, rootPrefix, pagesPrefix, userName, userInitials, isLoggedIn });
    }

    container.innerHTML = sidebarHTML;

    // Re-initialize Lucide icons for the injected HTML
    if (window.lucide) {
        lucide.createIcons();
    }

    // Fetch and display notification count and balance
    if (isLoggedIn) {
        fetchNotificationsCount();
        fetchBalance();
        checkVerificationStatus();
    }
}

async function fetchBalance() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        
        const res = await fetch('http://127.0.0.1:5001/get_balance', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!res.ok) return;
        const data = await res.json();
        
        const balanceEl = document.getElementById('sidebar-balance');
        if (balanceEl) {
            balanceEl.textContent = data.balance + ' PTS';
        }
    } catch (e) {
        console.error("Failed to load balance", e);
    }
}

async function fetchNotificationsCount() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        
        const res = await fetch('http://127.0.0.1:5001/notifications', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!res.ok) return;
        const notifications = await res.json();
        
        // Count unseen notifications
        const unseenCount = notifications.filter(n => !n.seen).length;
        
        const badge = document.getElementById('global-notif-badge');
        if (badge && unseenCount > 0) {
            badge.textContent = unseenCount;
            badge.style.display = 'inline-block';
        } else if (badge) {
            badge.style.display = 'none';
        }
    } catch (e) {
        console.error("Failed to load notifications count", e);
    }
}

async function checkVerificationStatus() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        const res = await fetch('http://127.0.0.1:5001/me', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!res.ok) return;
        const user = await res.json();
        
        if (user.is_verified === 0) {
            injectVerificationBanner();
        }
    } catch (e) {
        console.error("Failed to check verification status", e);
    }
}

function injectVerificationBanner() {
    // Check if banner already exists
    if (document.getElementById('verification-banner')) return;
    
    // Do not show on login or register pages
    const path = window.location.pathname;
    if (path.includes('login.html') || path.includes('register.html') || path.includes('verify.html')) return;

    const banner = document.createElement('div');
    banner.id = 'verification-banner';
    banner.style.cssText = `
        background: var(--warning-amber);
        color: #000;
        padding: 12px 24px;
        font-family: var(--font-mono);
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        z-index: 1000;
        position: relative;
    `;
    
    banner.innerHTML = `
        <i data-lucide="alert-triangle" style="width: 18px; height: 18px;"></i>
        <span>⚠ VERIFY_EMAIL — CHECK_INBOX OR</span>
        <a href="#" id="resend-verification-link" style="
            background: #000;
            color: #fff;
            padding: 6px 16px;
            border-radius: 4px;
            text-decoration: none;
            margin-left: 12px;
            font-size: 0.7rem;
            font-weight: 900;
            display: inline-flex;
            align-items: center;
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.2s;
        ">RESEND_LINK</a>
    `;
    
    // Inject at the top of the workspace if it exists, else at the top of body
    const workspace = document.querySelector('.workspace');
    if (workspace) {
        workspace.prepend(banner);
    } else {
        document.body.prepend(banner);
    }
    
    if (window.lucide) lucide.createIcons();
    
    document.getElementById('resend-verification-link').onclick = async (e) => {
        e.preventDefault();
        const link = e.target;
        const originalText = link.textContent;
        link.textContent = 'SENDING...';
        
        try {
            const token = localStorage.getItem('access_token');
            const res = await fetch('http://127.0.0.1:5001/resend_verification', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const data = await res.json();
            if (res.ok) {
                link.textContent = 'EMAIL_SENT';
                setTimeout(() => { link.textContent = 'RESEND_LINK'; }, 3000);
            } else {
                alert(data.message || 'Failed to resend email.');
                link.textContent = 'ERROR';
                setTimeout(() => { link.textContent = 'RESEND_LINK'; }, 3000);
            }
        } catch (err) {
            alert('System error.');
            link.textContent = 'ERROR';
            setTimeout(() => { link.textContent = 'RESEND_LINK'; }, 3000);
        }
    };
}

/**
 * Build the sidebar for logged-in app pages (dashboard, chat, leaderboard, etc.)
 */
function buildAppSidebar({ activePage, rootPrefix, pagesPrefix, userName, userInitials, isLoggedIn }) {
    return `
    <aside class="sidebar-nav">
        <a href="${rootPrefix}index.html" class="brand-header">
            <div class="brand-icon">
                <i data-lucide="terminal" style="width: 18px; height: 18px;"></i>
            </div>
            <div class="brand-name">StudentsHelper</div>
        </a>

        <div class="nav-menu">
            <div class="nav-section">
                <h4>Workspace</h4>
                <a href="${pagesPrefix}dashboard.html" class="nav-item ${activePage === 'dashboard' ? 'active' : ''}">
                    <i data-lucide="cpu" style="width: 18px; height: 18px;"></i>
                    <span>Overview</span>
                </a>
                <a href="${pagesPrefix}community-chat.html" class="nav-item ${activePage === 'community' ? 'active accent-blue' : ''}">
                    <i data-lucide="radio" style="width: 18px; height: 18px;"></i>
                    <span>Network</span>
                    <span class="nav-badge">3</span>
                </a>
                <a href="${pagesPrefix}leaderboard.html" class="nav-item ${activePage === 'leaderboard' ? 'active accent-blue' : ''}">
                    <i data-lucide="bar-chart-2" style="width: 18px; height: 18px;"></i>
                    <span>Ledger</span>
                </a>
            </div>

            <div class="nav-section">
                <h4>Operations</h4>
                <a href="${pagesPrefix}my-requests.html" class="nav-item ${activePage === 'my-requests' ? 'active' : ''}">
                    <i data-lucide="folder-open" style="width: 18px; height: 18px;"></i>
                    <span>Active Bounties</span>
                </a>
                <a href="${pagesPrefix}help-others.html" class="nav-item ${activePage === 'help-others' ? 'active' : ''}">
                    <i data-lucide="crosshair" style="width: 18px; height: 18px;"></i>
                    <span>Hunt Mode</span>
                </a>
            </div>

            <div class="nav-section">
                <h4>System</h4>
                <a href="${pagesPrefix}notifications.html" class="nav-item ${activePage === 'notifications' ? 'active accent-purple' : ''}">
                    <i data-lucide="bell" style="width: 18px; height: 18px;"></i>
                    <span>Alerts</span>
                    <span class="nav-badge" id="global-notif-badge" style="display:none; background:var(--danger-red); color:white;">0</span>
                </a>
                <a href="${pagesPrefix}profile.html" class="nav-item ${activePage === 'profile' ? 'active accent-purple' : ''}">
                    <i data-lucide="user" style="width: 18px; height: 18px;"></i>
                    <span>Identity</span>
                </a>
                <a href="${pagesPrefix}settings.html" class="nav-item ${activePage === 'settings' ? 'active accent-purple' : ''}">
                    <i data-lucide="sliders" style="width: 18px; height: 18px;"></i>
                    <span>Config</span>
                </a>
            </div>
        </div>

        <div class="sidebar-footer" onclick="window.location.href='${pagesPrefix}profile.html'" title="View Profile">
            <div class="user-avatar" id="sidebarAvatar">${userInitials}</div>
            <div class="user-info">
                <div class="user-name" id="sidebarName">${userName}</div>
                <div class="user-role" id="sidebar-balance">LOADING...</div>
            </div>
            <i data-lucide="power" onclick="event.stopPropagation(); logout()" style="color: var(--danger-red); width: 16px; height: 16px; margin-left: auto; cursor: pointer;" title="Logout"></i>
        </div>
    </aside>`;
}

/**
 * Build the sidebar for public pages (about, contact)
 */
function buildPublicSidebar({ activePage, rootPrefix, pagesPrefix, userName, userInitials, isLoggedIn }) {
    return `
    <aside class="sidebar-nav">
        <a href="${rootPrefix}index.html" class="brand-header">
            <div class="brand-icon">
                <i data-lucide="terminal" style="width: 18px; height: 18px;"></i>
            </div>
            <div class="brand-name">StudentsHelper</div>
        </a>

        <div class="nav-menu">
            <div class="nav-section">
                <h4>Public Net</h4>
                <a href="${rootPrefix}index.html" class="nav-item ${activePage === 'home' ? 'active' : ''}">
                    <i data-lucide="globe" style="width: 18px; height: 18px;"></i>
                    <span>Grid</span>
                </a>
                <a href="${pagesPrefix}about.html" class="nav-item ${activePage === 'about' ? 'active accent-purple' : ''}">
                    <i data-lucide="info" style="width: 18px; height: 18px;"></i>
                    <span>Sys.Origin</span>
                </a>
                <a href="${pagesPrefix}contact.html" class="nav-item ${activePage === 'contact' ? 'active accent-blue' : ''}">
                    <i data-lucide="mail" style="width: 18px; height: 18px;"></i>
                    <span>Transmit</span>
                </a>
            </div>

            <div class="nav-section">
                <h4>Actions</h4>
                <a href="${pagesPrefix}login.html" class="nav-item ${activePage === 'login' ? 'active' : ''}">
                    <i data-lucide="log-in" style="width: 18px; height: 18px;"></i>
                    <span>Authenticate</span>
                </a>
                <a href="${pagesPrefix}register.html" class="nav-item ${activePage === 'register' ? 'active' : ''}">
                    <i data-lucide="user-plus" style="width: 18px; height: 18px;"></i>
                    <span>Initialize Node</span>
                </a>
            </div>
        </div>

        <div class="sidebar-footer" onclick="location.href='${pagesPrefix}login.html'">
            <div class="user-avatar">${isLoggedIn ? userInitials : '<i data-lucide="user"></i>'}</div>
            <div class="user-info">
                <div class="user-name">${isLoggedIn ? userName : 'Guest User'}</div>
                <div class="user-role">${isLoggedIn ? 'NODE_LVL_4' : 'UNVERIFIED_NODE'}</div>
            </div>
            <i data-lucide="arrow-right" style="color: var(--text-tertiary); width: 16px; height: 16px; margin-left: auto;"></i>
        </div>
    </aside>`;
}

/**
 * Get initials from a name string
 */
function getInitials(name) {
    if (!name) return '?';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return parts[0].substring(0, 2).toUpperCase();
}

/**
 * Logout function
 */
function logout() {
    localStorage.removeItem('loggedInUser');
    localStorage.removeItem('currentUser');

    // Navigate to index
    const inPages = window.location.pathname.includes('/pages/');
    window.location.href = inPages ? '../index.html' : 'index.html';
}
