/**
 * Dashboard Component — Shows aggregate stats, room availability, and recent reservations.
 */
const DashboardComponent = {
    async render() {
        const content = document.getElementById('content-area');
        content.innerHTML = `
            <div class="stats-grid" id="stats-grid">
                <div class="stat-card blue"><div class="spinner" style="margin:20px auto"></div></div>
                <div class="stat-card green"><div class="spinner" style="margin:20px auto"></div></div>
                <div class="stat-card orange"><div class="spinner" style="margin:20px auto"></div></div>
                <div class="stat-card purple"><div class="spinner" style="margin:20px auto"></div></div>
            </div>
            <div class="section-grid">
                <div class="card" id="availability-card">
                    <div class="card-header">
                        <div><h3 class="card-title">Room Availability</h3>
                        <p class="card-subtitle">Per hotel breakdown</p></div>
                    </div>
                    <div id="availability-content"><div class="loading-spinner"><div class="spinner"></div></div></div>
                </div>
                <div class="card" id="recent-card">
                    <div class="card-header">
                        <div><h3 class="card-title">Recent Reservations</h3>
                        <p class="card-subtitle">Latest bookings</p></div>
                    </div>
                    <div id="recent-content"><div class="loading-spinner"><div class="spinner"></div></div></div>
                </div>
            </div>
        `;

        // Load data in parallel
        this.loadStats();
        this.loadAvailability();
        this.loadRecentReservations();
    },

    async loadStats() {
        try {
            const stats = await API.getStats();
            document.getElementById('stats-grid').innerHTML = `
                <div class="stat-card blue">
                    <span class="stat-icon">🏨</span>
                    <div class="stat-value">${stats.hotels}</div>
                    <div class="stat-label">Hotels</div>
                </div>
                <div class="stat-card green">
                    <span class="stat-icon">🛏️</span>
                    <div class="stat-value">${stats.rooms}</div>
                    <div class="stat-label">Rooms</div>
                </div>
                <div class="stat-card orange">
                    <span class="stat-icon">👤</span>
                    <div class="stat-value">${stats.guests}</div>
                    <div class="stat-label">Guests</div>
                </div>
                <div class="stat-card purple">
                    <span class="stat-icon">📋</span>
                    <div class="stat-value">${stats.reservations}</div>
                    <div class="stat-label">Reservations</div>
                </div>
            `;
        } catch (e) {
            document.getElementById('stats-grid').innerHTML =
                `<div class="card" style="grid-column:1/-1"><p class="empty-state-text">⚠️ ${e.message}</p></div>`;
        }
    },

    async loadAvailability() {
        try {
            const data = await API.getRoomAvailability();
            const el = document.getElementById('availability-content');
            if (!data.length) {
                el.innerHTML = '<div class="empty-state"><p class="empty-state-text">No room data available</p></div>';
                return;
            }
            el.innerHTML = data.map(h => {
                const total = h.total || 1;
                const aPct = (h.available / total * 100).toFixed(0);
                const oPct = (h.occupied / total * 100).toFixed(0);
                const mPct = (h.maintenance / total * 100).toFixed(0);
                return `
                    <div style="margin-bottom:18px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                            <strong>${h.hotel_name}</strong>
                            <span style="color:var(--text-muted);font-size:0.82rem">${h.total} rooms</span>
                        </div>
                        <div class="avail-bar">
                            <div class="avail-segment avail-available" style="width:${aPct}%"></div>
                            <div class="avail-segment avail-occupied" style="width:${oPct}%"></div>
                            <div class="avail-segment avail-maintenance" style="width:${mPct}%"></div>
                        </div>
                        <div class="avail-legend">
                            <span class="leg-avail">${h.available} Available</span>
                            <span class="leg-occ">${h.occupied} Occupied</span>
                            <span class="leg-maint">${h.maintenance} Maintenance</span>
                        </div>
                    </div>
                `;
            }).join('');
        } catch (e) {
            document.getElementById('availability-content').innerHTML =
                `<p class="empty-state-text">⚠️ ${e.message}</p>`;
        }
    },

    async loadRecentReservations() {
        try {
            const data = await API.getRecentReservations();
            const el = document.getElementById('recent-content');
            if (!data.length) {
                el.innerHTML = '<div class="empty-state"><p class="empty-state-text">No reservations yet</p></div>';
                return;
            }
            el.innerHTML = `
                <div class="table-wrapper">
                    <table>
                        <thead><tr>
                            <th>ID</th><th>Guest</th><th>Room</th><th>Hotel</th><th>Check In</th><th>Status</th>
                        </tr></thead>
                        <tbody>
                            ${data.map(r => `
                                <tr>
                                    <td>${r.res_id}</td>
                                    <td>${r.guest_name}</td>
                                    <td>${r.room_no}</td>
                                    <td>${r.hotel_name}</td>
                                    <td>${r.check_in_date || '-'}</td>
                                    <td>${App.statusBadge(r.status)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (e) {
            document.getElementById('recent-content').innerHTML =
                `<p class="empty-state-text">⚠️ ${e.message}</p>`;
        }
    }
};
