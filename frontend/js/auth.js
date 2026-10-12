/**
 * Auth — Client-side authentication module.
 * Manages user sessions in localStorage with role-based access control.
 *
 * Roles:
 *   - admin: Full access to all dashboard sections
 *   - guest: Access to book hotel services (rooms, reservations, recommendations)
 */
const Auth = {
    SESSION_KEY: 'hotelms_session',

    /** Admin credentials (in a real app these live server-side) */
    ADMIN_USER: 'admin',
    ADMIN_PASS: 'admin123',

    /**
     * Authenticate an admin user.
     * @param {string} username
     * @param {string} password
     * @returns {{ success: boolean, error?: string }}
     */
    loginAdmin(username, password) {
        if (!username || !password) {
            return { success: false, error: 'Please enter both username and password' };
        }
        if (username !== this.ADMIN_USER || password !== this.ADMIN_PASS) {
            return { success: false, error: 'Invalid admin credentials' };
        }

        const session = {
            role: 'admin',
            username: this.ADMIN_USER,
            displayName: 'Administrator',
            loginTime: Date.now(),
        };
        localStorage.setItem(this.SESSION_KEY, JSON.stringify(session));
        return { success: true };
    },

    /**
     * Register / log in a guest user.
     * Communicates with backend /api/guests/login to create via Cypher queries
     * or authenticate an existing guest node in Neo4j.
     * @param {object|string} guestData
     * @param {string} [email]
     * @param {string} [phone]
     * @param {string} [nationality]
     * @param {string} [gender]
     * @returns {Promise<{ success: boolean, guest?: object, isNew?: boolean, error?: string }>}
     */
    async loginGuest(guestData, email, phone, nationality, gender) {
        let payload = {};
        if (typeof guestData === 'object' && guestData !== null) {
            payload = { ...guestData };
        } else {
            payload = {
                name: (guestData || '').trim(),
                email: (email || '').trim(),
                phone: (phone || '').trim(),
                nationality: (nationality || 'Indian').trim(),
                gender: gender || 'Other',
            };
        }

        if (!payload.guest_id && !payload.email && !payload.phone && !payload.contact_info && !payload.name) {
            return { success: false, error: 'Please enter your email address, phone, or guest ID' };
        }

        // Basic email check if provided
        if (payload.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email.trim())) {
            return { success: false, error: 'Please enter a valid email address' };
        }

        if (!payload.password) {
            return { success: false, error: 'Password is required to sign in or register' };
        }

        const contactInfo = payload.contact_info || payload.email || payload.phone || 'Not provided';

        try {
            // Call backend API /api/guests/login
            const requestBody = {
                guest_id: payload.guest_id || undefined,
                name: payload.name,
                password: payload.password,
                contact_info: contactInfo,
                email: payload.email,
                phone: payload.phone,
                nationality: payload.nationality || 'Indian',
                gender: payload.gender || 'Other',
                action: payload.action || undefined,
            };

            let res;
            if (window.API && typeof window.API.loginGuest === 'function') {
                res = await window.API.loginGuest(requestBody);
            } else {
                const response = await fetch('/api/guests/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody),
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Login failed');
                }
                res = data;
            }

            if (!res || !res.success || !res.guest) {
                return { success: false, error: (res && res.error) || 'Failed to authenticate guest' };
            }

            const guest = res.guest;
            const session = {
                role: 'guest',
                guest_id: guest.guest_id,
                displayName: guest.name || payload.name,
                email: guest.contact_info || payload.email || '',
                phone: payload.phone || '',
                nationality: guest.nationality || payload.nationality || 'Indian',
                gender: guest.gender || payload.gender || 'Other',
                is_new: Boolean(res.is_new),
                loginTime: Date.now(),
            };
            localStorage.setItem(this.SESSION_KEY, JSON.stringify(session));
            return { success: true, guest, isNew: res.is_new };
        } catch (err) {
            console.error('Guest login error:', err);
            return { success: false, error: err.message || 'Cannot connect to server. Is backend running?' };
        }
    },

    /**
     * Get the current session, or null if not logged in.
     * @returns {object|null}
     */
    getSession() {
        try {
            const raw = localStorage.getItem(this.SESSION_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch {
            return null;
        }
    },

    /**
     * Whether the user is logged in.
     * @returns {boolean}
     */
    isLoggedIn() {
        return this.getSession() !== null;
    },

    /**
     * Whether the current user is an admin.
     * @returns {boolean}
     */
    isAdmin() {
        const session = this.getSession();
        return session?.role === 'admin';
    },

    /**
     * Whether the current user is a guest.
     * @returns {boolean}
     */
    isGuest() {
        const session = this.getSession();
        return session?.role === 'guest';
    },

    /**
     * Log the user out and redirect to login.
     */
    logout() {
        localStorage.removeItem(this.SESSION_KEY);
        window.location.href = '/login';
    },

    /**
     * Guard: redirect to login if not authenticated.
     */
    requireAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = '/login';
            return false;
        }
        return true;
    },

    /**
     * Guard: redirect to dashboard if already authenticated (for login page).
     */
    redirectIfLoggedIn() {
        if (this.isLoggedIn()) {
            window.location.href = '/';
            return true;
        }
        return false;
    },

    /**
     * Sections accessible by each role.
     */
    ROLE_ACCESS: {
        admin: ['dashboard', 'hotels', 'rooms', 'guests', 'reservations', 'staff', 'recommendations', 'graph'],
        guest: ['dashboard', 'hotels', 'rooms', 'guests', 'reservations', 'recommendations', 'graph'],
    },

    /**
     * Whether the current user can access a given section.
     * @param {string} section
     * @returns {boolean}
     */
    canAccess(section) {
        const session = this.getSession();
        if (!session) return false;
        const allowed = this.ROLE_ACCESS[session.role] || [];
        return allowed.includes(section);
    },
};
