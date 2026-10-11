/**
 * Hotels Component — List hotels and view their rooms and departments.
 */
const HotelsComponent = {
    async render() {
        const content = document.getElementById('content-area');
        content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading hotels...</p></div>';

        try {
            const hotels = await API.getHotels();
            if (!hotels.length) {
                content.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🏨</div><p class="empty-state-text">No hotels found</p></div>';
                return;
            }

            content.innerHTML = `
                <div class="stats-grid">
                    ${hotels.map(h => `
                        <div class="stat-card blue clickable-row" onclick="HotelsComponent.showDetail('${h.hotel_id}')" style="cursor:pointer">
                            <div style="display:flex;justify-content:space-between;align-items:start">
                                <span class="stat-icon">🏨</span>
                                <span class="rating">${'★'.repeat(Math.round(h.rating))}${'☆'.repeat(5 - Math.round(h.rating))}</span>
                            </div>
                            <div class="stat-value" style="font-size:1.3rem;margin-top:8px">${h.name}</div>
                            <div style="color:var(--text-secondary);font-size:0.85rem;margin-top:4px">📍 ${h.location}</div>
                            <div style="display:flex;gap:16px;margin-top:12px;font-size:0.82rem;color:var(--text-muted)">
                                <span>🛏️ ${h.room_count} rooms</span>
                                <span>🏢 ${h.dept_count} depts</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } catch (e) {
            content.innerHTML = `<div class="empty-state"><p class="empty-state-text">⚠️ ${e.message}</p></div>`;
        }
    },

    async showDetail(hotelId) {
        try {
            const hotel = await API.getHotel(hotelId);
            const body = `
                <ul class="detail-list">
                    <li><span class="detail-label">Hotel ID</span><span class="detail-value">${hotel.hotel_id}</span></li>
                    <li><span class="detail-label">Name</span><span class="detail-value">${hotel.name}</span></li>
                    <li><span class="detail-label">Location</span><span class="detail-value">${hotel.location}</span></li>
                    <li><span class="detail-label">Rating</span><span class="detail-value rating">${'★'.repeat(Math.round(hotel.rating))}${'☆'.repeat(5 - Math.round(hotel.rating))} ${hotel.rating}</span></li>
                </ul>

                <h4 style="margin:20px 0 12px;color:var(--accent-blue)">🛏️ Rooms (${hotel.rooms.length})</h4>
                ${hotel.rooms.length ? `
                    <div class="table-wrapper">
                        <table>
                            <thead><tr><th>Room</th><th>Category</th><th>Rent</th><th>Status</th></tr></thead>
                            <tbody>
                                ${hotel.rooms.map(r => `
                                    <tr>
                                        <td>${r.room_no}</td>
                                        <td>${r.category}</td>
                                        <td>₹${r.rent?.toLocaleString()}</td>
                                        <td>${App.statusBadge(r.status)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                ` : '<p class="empty-state-text">No rooms</p>'}

                <h4 style="margin:20px 0 12px;color:var(--accent-purple)">🏢 Departments (${hotel.departments.length})</h4>
                ${hotel.departments.length ? `
                    <div class="table-wrapper">
                        <table>
                            <thead><tr><th>ID</th><th>Role</th><th>Head</th><th>Contact</th></tr></thead>
                            <tbody>
                                ${hotel.departments.map(d => `
                                    <tr>
                                        <td>${d.dept_id}</td>
                                        <td>${d.d_role}</td>
                                        <td>${d.d_head}</td>
                                        <td>${d.contact_info}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                ` : '<p class="empty-state-text">No departments</p>'}
            `;
            App.showModal(`${hotel.name}`, body);
        } catch (e) {
            App.toast(e.message, 'error');
        }
    }
};
