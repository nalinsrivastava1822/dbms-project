/**
 * Guests Component — Add, list, search guests and view reservation history.
 */
const GuestsComponent = {
    async render() {
        const content = document.getElementById('content-area');
        content.innerHTML = `
            <div class="action-bar">
                <div></div>
                <button class="btn btn-primary" onclick="GuestsComponent.showAddForm()" id="btn-add-guest">+ Add Guest</button>
            </div>
            <div class="search-bar">
                <div class="form-group">
                    <label class="form-label">Name</label>
                    <input type="text" class="form-input" id="guest-search-name" placeholder="Search by name...">
                </div>
                <div class="form-group">
                    <label class="form-label">Nationality</label>
                    <input type="text" class="form-input" id="guest-search-nat" placeholder="e.g. Indian">
                </div>
                <button class="btn btn-secondary" onclick="GuestsComponent.search()" style="margin-top:auto">Search</button>
            </div>
            <div class="card">
                <div id="guests-table"><div class="loading-spinner"><div class="spinner"></div></div></div>
            </div>
        `;
        this.loadGuests();
    },

    async loadGuests() {
        try {
            const guests = await API.getGuests();
            this.renderTable(guests);
        } catch (e) {
            document.getElementById('guests-table').innerHTML = `<p class="empty-state-text">⚠️ ${e.message}</p>`;
        }
    },

    async search() {
        const params = {
            name: document.getElementById('guest-search-name').value,
            nationality: document.getElementById('guest-search-nat').value,
        };
        try {
            const guests = await API.searchGuests(params);
            this.renderTable(guests);
            App.toast(`Found ${guests.length} guests`, 'info');
        } catch (e) {
            App.toast(e.message, 'error');
        }
    },

    renderTable(guests) {
        const el = document.getElementById('guests-table');
        if (!guests.length) {
            el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">👤</div><p class="empty-state-text">No guests found</p></div>';
            return;
        }
        el.innerHTML = `
            <div class="table-wrapper">
                <table>
                    <thead><tr>
                        <th>ID</th><th>Name</th><th>Contact</th><th>Nationality</th><th>Gender</th><th>Reservations</th><th>Action</th>
                    </tr></thead>
                    <tbody>
                        ${guests.map(g => `
                            <tr class="clickable-row" onclick="GuestsComponent.showDetail('${g.guest_id}')">
                                <td>${g.guest_id}</td>
                                <td><strong>${g.name}</strong></td>
                                <td>${g.contact_info}</td>
                                <td>${g.nationality}</td>
                                <td>${g.gender}</td>
                                <td><span class="badge badge-active">${g.reservation_count}</span></td>
                                <td><button class="btn btn-sm btn-secondary" onclick="event.stopPropagation();GuestsComponent.showDetail('${g.guest_id}')">View</button></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    async showDetail(guestId) {
        try {
            const guest = await API.getGuest(guestId);
            const body = `
                <ul class="detail-list">
                    <li><span class="detail-label">Guest ID</span><span class="detail-value">${guest.guest_id}</span></li>
                    <li><span class="detail-label">Name</span><span class="detail-value">${guest.name}</span></li>
                    <li><span class="detail-label">Contact</span><span class="detail-value">${guest.contact_info}</span></li>
                    <li><span class="detail-label">Nationality</span><span class="detail-value">${guest.nationality}</span></li>
                    <li><span class="detail-label">Gender</span><span class="detail-value">${guest.gender}</span></li>
                </ul>

                <h4 style="margin:20px 0 12px;color:var(--accent-blue)">📋 Reservation History (${guest.reservations.length})</h4>
                ${guest.reservations.length ? `
                    <div class="table-wrapper">
                        <table>
                            <thead><tr><th>ID</th><th>Hotel</th><th>Room</th><th>Check In</th><th>Check Out</th><th>Status</th></tr></thead>
                            <tbody>
                                ${guest.reservations.map(r => `
                                    <tr>
                                        <td>${r.res_id}</td>
                                        <td>${r.hotel_name}</td>
                                        <td>${r.room_no} (${r.category})</td>
                                        <td>${r.check_in_date || '-'}</td>
                                        <td>${r.check_out_date || '-'}</td>
                                        <td>${App.statusBadge(r.status)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                ` : '<p class="empty-state-text">No reservations yet</p>'}
            `;
            App.showModal(`Guest: ${guest.name}`, body);
        } catch (e) {
            App.toast(e.message, 'error');
        }
    },

    showAddForm() {
        const body = `
            <form id="add-guest-form" onsubmit="GuestsComponent.submitAdd(event)">
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Guest ID</label>
                        <input type="text" class="form-input" id="new-guest-id" required placeholder="e.g. G009">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Name</label>
                        <input type="text" class="form-input" id="new-guest-name" required placeholder="Full name">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Contact</label>
                        <input type="text" class="form-input" id="new-guest-contact" required placeholder="Phone number">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Nationality</label>
                        <input type="text" class="form-input" id="new-guest-nat" required placeholder="e.g. Indian">
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">Gender</label>
                    <select class="form-select" id="new-guest-gender" required>
                        <option value="">Select</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;margin-top:8px">Add Guest</button>
            </form>
        `;
        App.showModal('Add New Guest', body);
    },

    async submitAdd(e) {
        e.preventDefault();
        const data = {
            guest_id: document.getElementById('new-guest-id').value.trim(),
            name: document.getElementById('new-guest-name').value.trim(),
            contact_info: document.getElementById('new-guest-contact').value.trim(),
            nationality: document.getElementById('new-guest-nat').value.trim(),
            gender: document.getElementById('new-guest-gender').value,
        };
        try {
            await API.createGuest(data);
            App.toast(`Guest ${data.name} added!`, 'success');
            App.closeModal();
            this.loadGuests();
        } catch (e) {
            App.toast(e.message, 'error');
        }
    }
};
