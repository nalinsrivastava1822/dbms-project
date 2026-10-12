/**
 * API Client — Centralized HTTP client for the Hotel Management API.
 * All API calls go through this module for consistency.
 */
const API = {
    BASE_URL: '',

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.BASE_URL}${endpoint}`, {
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options,
            });

            // Extract real-time Cypher query traces from backend header
            const traceHeader = response.headers.get('X-Backend-Trace');
            if (traceHeader && window.QueryInspector && typeof window.QueryInspector.addTraces === 'function') {
                try {
                    const decoded = decodeURIComponent(escape(atob(traceHeader)));
                    const traces = JSON.parse(decoded);
                    window.QueryInspector.addTraces(traces);
                } catch (e) {
                    try {
                        const traces = JSON.parse(atob(traceHeader));
                        window.QueryInspector.addTraces(traces);
                    } catch (_) {}
                }
            }

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }
            return data;
        } catch (error) {
            if (error.message.includes('Failed to fetch')) {
                throw new Error('Cannot connect to server. Is the backend running?');
            }
            throw error;
        }
    },

    // Dashboard
    getStats: () => API.request('/api/dashboard/stats'),
    getRoomAvailability: () => API.request('/api/dashboard/room-availability'),
    getRecentReservations: () => API.request('/api/dashboard/recent-reservations'),
    getRevenueAnalytics: () => API.request('/api/dashboard/revenue-analytics'),

    // Hotels
    getHotels: () => API.request('/api/hotels/'),
    getHotel: (id) => API.request(`/api/hotels/${id}`),
    getHotelRooms: (id) => API.request(`/api/hotels/${id}/rooms`),
    getHotelDepartments: (id) => API.request(`/api/hotels/${id}/departments`),

    // Rooms
    getRooms: () => API.request('/api/rooms/'),
    searchRooms: (params) => {
        const query = new URLSearchParams();
        Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, v); });
        return API.request(`/api/rooms/search?${query.toString()}`);
    },
    getCategories: () => API.request('/api/rooms/categories'),
    createRoom: (data) => API.request('/api/rooms/', { method: 'POST', body: JSON.stringify(data) }),
    updateRoomStatus: (roomNo, status) => API.request(`/api/rooms/${roomNo}/status`, {
        method: 'PATCH', body: JSON.stringify({ status }),
    }),

    // Guests
    getGuests: () => API.request('/api/guests/'),
    searchGuests: (params) => {
        const query = new URLSearchParams();
        Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, v); });
        return API.request(`/api/guests/search?${query.toString()}`);
    },
    getGuest: (id, callerGuestId) => {
        const q = callerGuestId ? `?caller_guest_id=${encodeURIComponent(callerGuestId)}` : '';
        return API.request(`/api/guests/${id}${q}`);
    },
    getGuestReservations: (id, callerGuestId) => {
        const q = callerGuestId ? `?caller_guest_id=${encodeURIComponent(callerGuestId)}` : '';
        return API.request(`/api/guests/${id}/reservations${q}`);
    },
    createGuest: (data) => API.request('/api/guests/', { method: 'POST', body: JSON.stringify(data) }),
    loginGuest: (data) => API.request('/api/guests/login', { method: 'POST', body: JSON.stringify(data) }),
    getNextGuestId: () => API.request('/api/guests/next-id'),

    // Reservations
    getReservations: (guestId, callerGuestId) => {
        const params = new URLSearchParams();
        if (guestId) params.set('guest_id', guestId);
        if (callerGuestId) params.set('caller_guest_id', callerGuestId);
        const qs = params.toString() ? `?${params.toString()}` : '';
        return API.request(`/api/reservations/${qs}`);
    },
    getNextReservationId: () => API.request('/api/reservations/next-id'),
    createReservation: (data) => API.request('/api/reservations/', { method: 'POST', body: JSON.stringify(data) }),
    cancelReservation: (id, callerGuestId) => {
        const q = callerGuestId ? `?caller_guest_id=${encodeURIComponent(callerGuestId)}` : '';
        return API.request(`/api/reservations/${id}/cancel${q}`, { method: 'POST' });
    },

    // Staff
    getStaff: () => API.request('/api/staff/'),
    createStaff: (data) => API.request('/api/staff/', { method: 'POST', body: JSON.stringify(data) }),
    getStaffByDepartment: (deptId) => {
        const query = deptId ? `?dept_id=${deptId}` : '';
        return API.request(`/api/staff/by-department${query}`);
    },
    getStaffReservations: (id) => API.request(`/api/staff/${id}/reservations`),


    // Recommendations
    recommendHotels: (guestId) => API.request(`/api/recommendations/hotels/${guestId}`),
    recommendRooms: (guestId) => API.request(`/api/recommendations/rooms/${guestId}`),
    popularByNationality: (nat) => API.request(`/api/recommendations/popular-by-nationality/${nat}`),
    guestJourney: (guestId) => API.request(`/api/recommendations/guest-journey/${guestId}`),

    // Graph Topology
    getGraphData: () => API.request('/api/graph/data'),

    // Health
    health: () => API.request('/api/health'),

    // Query Inspector
    getQueryHistory: () => API.request('/api/query-inspector/history'),
    clearQueryHistory: () => API.request('/api/query-inspector/clear', { method: 'POST' }),
};
