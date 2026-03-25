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
    const userName = user.name || user.email?.split('@')[0] || 'Guest User';
    const userInitials = getInitials(userName);
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

        <div class="sidebar-footer" onclick="logout()">
            <div class="user-avatar" id="sidebarAvatar">${userInitials}</div>
            <div class="user-info">
                <div class="user-name" id="sidebarName">${userName}</div>
                <div class="user-role">NODE_LVL_4</div>
            </div>
            <i data-lucide="power" style="color: var(--danger-red); width: 16px; height: 16px; margin-left: auto;"></i>
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
