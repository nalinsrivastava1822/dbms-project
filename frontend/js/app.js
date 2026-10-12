/**
 * App — Main application controller.
 * Handles routing, navigation, modals, toasts, auth, and initialization.
 */
const App = {
    currentSection: 'dashboard',

    components: {
        dashboard: DashboardComponent,
        hotels: HotelsComponent,
        rooms: RoomsComponent,
        guests: GuestsComponent,
        reservations: ReservationsComponent,
        staff: StaffComponent,
        recommendations: RecommendationsComponent,
        graph: GraphVisualizerComponent,
    },

    titles: {
        dashboard: 'Dashboard',
        hotels: 'Hotels',
        rooms: 'Rooms',
        guests: 'Guests',
        reservations: 'Reservations',
        staff: 'Staff & Departments',
        recommendations: 'Graph Recommendations',
        graph: 'Interactive Graph Topology Visualizer',
    },

    init() {
        // --- Auth guard ---
        if (!Auth.requireAuth()) return;

        // --- Display user info in top bar ---
        this.setupUserInfo();

        // --- Filter sidebar nav by role ---
        this.filterNavByRole();

        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                this.navigate(section);
            });
        });

        // Mobile menu
        document.getElementById('menu-toggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('open');
        });

        // Modal close
        document.getElementById('modal-close').addEventListener('click', () => this.closeModal());
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeModal();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeModal();
        });

        // Logout button
        document.getElementById('btn-logout').addEventListener('click', () => {
            Auth.logout();
        });

        // Check connection and navigate to dashboard
        this.checkConnection();
        this.navigate('dashboard');
    },

    /**
     * Show the logged-in user's name and role badge in the top bar.
     */
    setupUserInfo() {
        const session = Auth.getSession();
        if (!session) return;

        const roleBadge = document.getElementById('user-role-badge');
        const userName  = document.getElementById('user-name');

        if (session.role === 'admin') {
            roleBadge.textContent = 'ADMIN';
            roleBadge.classList.add('role-admin');
            userName.textContent = session.displayName || 'Administrator';
        } else {
            roleBadge.textContent = 'GUEST';
            roleBadge.classList.add('role-guest');
            userName.textContent = session.guest_id
                ? `${session.guest_id} · ${session.displayName}`
                : session.displayName || 'Guest';
        }
    },

    /**
     * Hide sidebar nav links the current role cannot access.
     */
    filterNavByRole() {
        document.querySelectorAll('.nav-link').forEach(link => {
            const section = link.dataset.section;
            if (!Auth.canAccess(section)) {
                link.closest('li').style.display = 'none';
            }
        });

        if (Auth.isGuest()) {
            this.titles.reservations = 'My Reservations';
            this.titles.rooms = 'Smart Room Booking';
            const resLink = document.getElementById('nav-reservations');
            if (resLink) resLink.innerHTML = '<span class="nav-icon">📋</span> My Reservations';
            const roomLink = document.getElementById('nav-rooms');
            if (roomLink) roomLink.innerHTML = '<span class="nav-icon">🛏️</span> Book Rooms';
        }
    },

    navigate(section) {
        if (!this.components[section]) return;

        // Role-based guard
        if (!Auth.canAccess(section)) {
            this.toast('You do not have access to this section', 'error');
            return;
        }

        this.currentSection = section;
        document.getElementById('page-title').textContent = this.titles[section] || section;

        // Update active nav
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        const activeLink = document.querySelector(`[data-section="${section}"]`);
        if (activeLink) activeLink.classList.add('active');

        // Close mobile sidebar
        document.getElementById('sidebar').classList.remove('open');

        // Render component
        const content = document.getElementById('content-area');
        content.style.animation = 'none';
        content.offsetHeight; // trigger reflow
        content.style.animation = 'fadeIn 0.3s ease';

        this.components[section].render();
    },

    async checkConnection() {
        const statusEl = document.getElementById('connection-status');
        try {
            const health = await API.health();
            if (health.status === 'healthy') {
                if (health.mode === 'live_neo4j') {
                    statusEl.innerHTML = '<span class="status-dot connected"></span> Neo4j Connected';
                } else {
                    statusEl.innerHTML = '<span class="status-dot connected" style="background:#10b981;"></span> Online (Graph Simulator)';
                    statusEl.title = 'In-Memory Graph Engine active. Connect local Neo4j or Neo4j Aura anytime for live database.';
                }
            } else {
                statusEl.innerHTML = '<span class="status-dot error"></span> DB Error';
            }
        } catch (e) {
            statusEl.innerHTML = '<span class="status-dot error"></span> Offline';
        }
    },

    // --- Utility Methods ---

    statusBadge(status) {
        if (!status) return '-';
        const cls = status.toLowerCase();
        return `<span class="badge badge-${cls}">${status}</span>`;
    },

    statusBadgeHTML(status) {
        if (!status) return '-';
        const cls = status.toLowerCase();
        return `<span class="badge badge-${cls}">${status}</span>`;
    },

    showModal(title, bodyHTML) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = bodyHTML;
        document.getElementById('modal-overlay').classList.add('active');
    },

    closeModal() {
        document.getElementById('modal-overlay').classList.remove('active');
    },

    toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
        toast.innerHTML = `<span>${icon}</span><span class="toast-message">${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    },
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => App.init());
