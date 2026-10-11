/**
 * Reservations Component — Create, list, and cancel reservations.
 */
const ReservationsComponent = {
    async render() {
        const content = document.getElementById('content-area');
        content.innerHTML = `
            <div class="action-bar">
                <div></div>
                <button class="btn btn-primary" onclick="ReservationsComponent.showCreateForm()" id="btn-new-reservation">+ New Reservation</button>
            </div>
            <div class="card">
                <div id="reservations-table"><div class="loading-spinner"><div class="spinner"></div></div></div>
            </div>
        `;
        this.loadReservations();
    },

    async loadReservations() {
        try {
            const reservations = await API.getReservations();
            const el = document.getElementById('reservations-table');
            if (!reservations.length) {
                el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><p class="empty-state-text">No reservations</p></div>';
                return;
            }
            el.innerHTML = `
                <div class="table-wrapper">
                    <table>
                        <thead><tr>
                            <th>ID</th><th>Guest</th><th>Room</th><th>Hotel</th><th>Category</th><th>Check In</th><th>Check Out</th><th>Staff</th><th>Status</th><th>Action</th>
                        </tr></thead>
                        <tbody>
                            ${reservations.map(r => `
                                <tr>
                                    <td><strong>${r.res_id}</strong></td>
                                    <td>${r.guest_name}</td>
                                    <td>${r.room_no}</td>
                                    <td>${r.hotel_name}</td>
                                    <td>${r.category || '-'}</td>
                                    <td>${r.check_in_date || '-'}</td>
                                    <td>${r.check_out_date || '-'}</td>
                                    <td>${r.staff_name || '-'}</td>
                                    <td>${App.statusBadge(r.status)}</td>
                                    <td>
                                        ${['Active', 'Confirmed'].includes(r.status) ?
                                            `<button class="btn btn-sm btn-danger" onclick="ReservationsComponent.cancel('${r.res_id}')">Cancel</button>` :
                                            '-'}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (e) {
            document.getElementById('reservations-table').innerHTML = `<p class="empty-state-text">⚠️ ${e.message}</p>`;
        }
    },

    async cancel(resId) {
        if (!confirm(`Cancel reservation ${resId}? This will free up the room.`)) return;
        try {
            await API.cancelReservation(resId);
            App.toast(`Reservation ${resId} cancelled`, 'success');
            this.loadReservations();
        } catch (e) {
            App.toast(e.message, 'error');
        }
    },

    async showCreateForm() {
        let guests, rooms, staff;
        try {
            [guests, rooms, staff] = await Promise.all([
                API.getGuests(), API.searchRooms({ status: 'Available' }), API.getStaff()
            ]);
        } catch (e) {
            App.toast(e.message, 'error');
            return;
        }

        const today = new Date().toISOString().split('T')[0];
        const body = `
            <form id="create-res-form" onsubmit="ReservationsComponent.submitCreate(event)">
                <div class="form-group">
                    <label class="form-label">Reservation ID</label>
                    <input type="text" class="form-input" id="new-res-id" required placeholder="e.g. R010">
                </div>
                <div class="form-group">
                    <label class="form-label">Guest</label>
                    <select class="form-select" id="new-res-guest" required>
                        <option value="">Select Guest</option>
                        ${guests.map(g => `<option value="${g.guest_id}">${g.name} (${g.guest_id})</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Room (Available Only)</label>
                    <select class="form-select" id="new-res-room" required>
                        <option value="">Select Room</option>
                        ${rooms.map(r => `<option value="${r.room_no}">${r.room_no} — ${r.hotel_name} (${r.category}, ₹${r.rent})</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Processing Staff</label>
                    <select class="form-select" id="new-res-staff" required>
                        <option value="">Select Staff</option>
                        ${staff.map(s => `<option value="${s.staff_id}">${s.name} — ${s.department}, ${s.hotel_name} (${s.staff_id})</option>`).join('')}
                    </select>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Check-In Date</label>
                        <input type="date" class="form-input" id="new-res-checkin" required min="${today}">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Check-Out Date</label>
                        <input type="date" class="form-input" id="new-res-checkout" required min="${today}">
                    </div>
                </div>
                <div id="res-form-error" class="form-error" style="margin-bottom:8px"></div>
                <button type="submit" class="btn btn-primary" style="width:100%">Create Reservation</button>
            </form>
        `;
        App.showModal('New Reservation', body);

        // Date validation
        document.getElementById('new-res-checkin').addEventListener('change', function () {
            document.getElementById('new-res-checkout').min = this.value;
        });
    },

    async submitCreate(e) {
        e.preventDefault();
        const errorEl = document.getElementById('res-form-error');
        errorEl.textContent = '';

        const checkin = document.getElementById('new-res-checkin').value;
        const checkout = document.getElementById('new-res-checkout').value;

        if (checkout <= checkin) {
            errorEl.textContent = 'Check-out date must be after check-in date.';
            return;
        }

        const data = {
            res_id: document.getElementById('new-res-id').value.trim(),
            guest_id: document.getElementById('new-res-guest').value,
            room_no: parseInt(document.getElementById('new-res-room').value),
            staff_id: document.getElementById('new-res-staff').value,
            check_in_date: checkin,
            check_out_date: checkout,
        };

        try {
            await API.createReservation(data);
            App.toast(`Reservation ${data.res_id} created!`, 'success');
            App.closeModal();
            this.loadReservations();
        } catch (e) {
            errorEl.textContent = e.message;
            App.toast(e.message, 'error');
        }
    }
};
