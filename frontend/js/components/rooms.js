/**
 * Rooms Component — List, search, add rooms and update status.
 */
const RoomsComponent = {
    async render() {
        const content = document.getElementById('content-area');
        content.innerHTML = `
            <div class="action-bar">
                <div></div>
                <button class="btn btn-primary" onclick="RoomsComponent.showAddForm()" id="btn-add-room">+ Add Room</button>
            </div>
            <div class="search-bar" id="room-search-bar">
                <div class="form-group">
                    <label class="form-label">Hotel</label>
                    <select class="form-select" id="search-hotel"><option value="">All Hotels</option></select>
                </div>
                <div class="form-group">
                    <label class="form-label">Category</label>
                    <select class="form-select" id="search-category"><option value="">All Categories</option></select>
                </div>
                <div class="form-group">
                    <label class="form-label">Max Rent</label>
                    <input type="number" class="form-input" id="search-rent" placeholder="e.g. 5000">
                </div>
                <div class="form-group">
                    <label class="form-label">Status</label>
                    <select class="form-select" id="search-status">
                        <option value="">All</option>
                        <option value="Available">Available</option>
                        <option value="Occupied">Occupied</option>
                        <option value="Maintenance">Maintenance</option>
                    </select>
                </div>
                <button class="btn btn-secondary" onclick="RoomsComponent.search()" style="margin-top:auto">Search</button>
            </div>
            <div class="card">
                <div id="rooms-table"><div class="loading-spinner"><div class="spinner"></div></div></div>
            </div>
        `;

        this.loadFilters();
        this.loadRooms();
    },

    async loadFilters() {
        try {
            const [hotels, categories] = await Promise.all([API.getHotels(), API.getCategories()]);
            const hotelSelect = document.getElementById('search-hotel');
            hotels.forEach(h => {
                hotelSelect.innerHTML += `<option value="${h.hotel_id}">${h.name}</option>`;
            });
            const catSelect = document.getElementById('search-category');
            categories.forEach(c => {
                catSelect.innerHTML += `<option value="${c.category_name}">${c.category_name} (₹${c.rent})</option>`;
            });
        } catch (e) { /* filters optional */ }
    },

    async loadRooms() {
        try {
            const rooms = await API.getRooms();
            this.renderTable(rooms);
        } catch (e) {
            document.getElementById('rooms-table').innerHTML = `<p class="empty-state-text">⚠️ ${e.message}</p>`;
        }
    },

    async search() {
        const params = {
            hotel_id: document.getElementById('search-hotel').value,
            category: document.getElementById('search-category').value,
            max_rent: document.getElementById('search-rent').value,
            status: document.getElementById('search-status').value,
        };
        try {
            const rooms = await API.searchRooms(params);
            this.renderTable(rooms);
            App.toast(`Found ${rooms.length} rooms`, 'info');
        } catch (e) {
            App.toast(e.message, 'error');
        }
    },

    renderTable(rooms) {
        const el = document.getElementById('rooms-table');
        if (!rooms.length) {
            el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🛏️</div><p class="empty-state-text">No rooms found</p></div>';
            return;
        }
        el.innerHTML = `
            <div class="table-wrapper">
                <table>
                    <thead><tr>
                        <th>Room</th><th>Hotel</th><th>Location</th><th>Category</th><th>Rent</th><th>Status</th><th>Action</th>
                    </tr></thead>
                    <tbody>
                        ${rooms.map(r => `
                            <tr>
                                <td><strong>${r.room_no}</strong></td>
                                <td>${r.hotel_name}</td>
                                <td>${r.location}</td>
                                <td>${r.category}</td>
                                <td>₹${r.rent?.toLocaleString()}</td>
                                <td>${App.statusBadge(r.status)}</td>
                                <td>
                                    <select class="form-select" style="width:auto;padding:4px 28px 4px 8px;font-size:0.78rem"
                                        onchange="RoomsComponent.updateStatus(${r.room_no}, this.value)">
                                        <option value="" disabled selected>Change</option>
                                        <option value="Available">Available</option>
                                        <option value="Occupied">Occupied</option>
                                        <option value="Maintenance">Maintenance</option>
                                    </select>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    async updateStatus(roomNo, status) {
        try {
            await API.updateRoomStatus(roomNo, status);
            App.toast(`Room ${roomNo} → ${status}`, 'success');
            this.loadRooms();
        } catch (e) {
            App.toast(e.message, 'error');
        }
    },

    async showAddForm() {
        const [hotels, categories] = await Promise.all([API.getHotels(), API.getCategories()]);
        const body = `
            <form id="add-room-form" onsubmit="RoomsComponent.submitAdd(event)">
                <div class="form-group">
                    <label class="form-label">Room Number</label>
                    <input type="number" class="form-input" id="new-room-no" required min="1" placeholder="e.g. 401">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Hotel</label>
                        <select class="form-select" id="new-room-hotel" required>
                            <option value="">Select Hotel</option>
                            ${hotels.map(h => `<option value="${h.hotel_id}">${h.name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Category</label>
                        <select class="form-select" id="new-room-cat" required>
                            <option value="">Select Category</option>
                            ${categories.map(c => `<option value="${c.category_name}">${c.category_name} (₹${c.rent})</option>`).join('')}
                        </select>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;margin-top:8px">Add Room</button>
            </form>
        `;
        App.showModal('Add New Room', body);
    },

    async submitAdd(e) {
        e.preventDefault();
        const data = {
            room_no: parseInt(document.getElementById('new-room-no').value),
            hotel_id: document.getElementById('new-room-hotel').value,
            category_name: document.getElementById('new-room-cat').value,
            status: 'Available',
        };
        try {
            await API.createRoom(data);
            App.toast(`Room ${data.room_no} added!`, 'success');
            App.closeModal();
            this.loadRooms();
        } catch (e) {
            App.toast(e.message, 'error');
        }
    }
};
