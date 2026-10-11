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
    getGuest: (id) => API.request(`/api/guests/${id}`),
    createGuest: (data) => API.request('/api/guests/', { method: 'POST', body: JSON.stringify(data) }),

    // Reservations
    getReservations: () => API.request('/api/reservations/'),
    createReservation: (data) => API.request('/api/reservations/', { method: 'POST', body: JSON.stringify(data) }),
    cancelReservation: (id) => API.request(`/api/reservations/${id}/cancel`, { method: 'POST' }),

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
};
