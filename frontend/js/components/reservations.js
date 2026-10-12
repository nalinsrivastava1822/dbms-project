/**
 * Reservations Component — Guest Self-Service Portal & Staff Management.
 */
const ReservationsComponent = {
    activePortalTab: 'upcoming',
    guestData: {
        upcoming: [],
        completed: [],
        cancelled: [],
    },
    allReservations: [],

    async render() {
        if (Auth.isGuest()) {
            await this.renderGuestPortal();
        } else {
            await this.renderAdminView();
        }
    },

    // =========================================================================
    // GUEST SELF-SERVICE PORTAL
    // =========================================================================
    async renderGuestPortal() {
        const session = Auth.getSession();
        const content = document.getElementById('content-area');

        content.innerHTML = `
            <div class="action-bar" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px">
                <div>
                    <h2 style="font-size:1.35rem;font-weight:700">My Reservations</h2>
                    <p style="color:var(--text-secondary);font-size:0.85rem">
                        Manage your stays, view booking references, and request cancellations
                    </p>
                </div>
                <div style="display:flex;gap:10px">
                    <button class="btn btn-secondary" onclick="ReservationsComponent.loadGuestPortalData()">
                        ↻ Refresh
                    </button>
                    <button class="btn btn-primary" onclick="App.navigate('rooms')">
                        + Book New Room
                    </button>
                </div>
            </div>

            <!-- Portal Tabs -->
            <div class="portal-tabs" id="portal-tab-bar">
                <button class="portal-tab-btn active" data-tab="upcoming" onclick="ReservationsComponent.switchTab('upcoming')">
                    📅 Upcoming Bookings <span class="badge-count" id="count-upcoming">0</span>
                </button>
                <button class="portal-tab-btn" data-tab="completed" onclick="ReservationsComponent.switchTab('completed')">
                    ✓ Completed Stays <span class="badge-count" id="count-completed">0</span>
                </button>
                <button class="portal-tab-btn" data-tab="cancelled" onclick="ReservationsComponent.switchTab('cancelled')">
                    ✕ Cancelled Bookings <span class="badge-count" id="count-cancelled">0</span>
                </button>
            </div>

            <!-- Reservations Container -->
            <div class="card">
                <div id="portal-content">
                    <div class="loading-spinner"><div class="spinner"></div></div>
                </div>
            </div>
        `;

        await this.loadGuestPortalData();
    },

    async loadGuestPortalData() {
        const session = Auth.getSession();
        if (!session || !session.guest_id) {
            document.getElementById('portal-content').innerHTML = `
                <div class="empty-state">
                    <p class="empty-state-text">⚠️ Guest session not authenticated. Please log in again.</p>
                </div>
            `;
            return;
        }

        try {
            const data = await API.getGuestReservations(session.guest_id, session.guest_id);
            this.guestData = {
                upcoming: data.upcoming || [],
                completed: data.completed || [],
                cancelled: data.cancelled || [],
            };

            // Update badge counts
            const upCount = document.getElementById('count-upcoming');
            const compCount = document.getElementById('count-completed');
            const canCount = document.getElementById('count-cancelled');
            if (upCount) upCount.textContent = this.guestData.upcoming.length;
            if (compCount) compCount.textContent = this.guestData.completed.length;
            if (canCount) canCount.textContent = this.guestData.cancelled.length;

            this.renderPortalTabContent(this.activePortalTab);
        } catch (err) {
            document.getElementById('portal-content').innerHTML = `
                <div class="empty-state">
                    <p class="empty-state-text">⚠️ ${err.message || 'Could not load your reservations'}</p>
                </div>
            `;
            App.toast(err.message, 'error');
        }
    },

    switchTab(tabName) {
        this.activePortalTab = tabName;
        document.querySelectorAll('.portal-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        this.renderPortalTabContent(tabName);
    },

    renderPortalTabContent(tabName) {
        const container = document.getElementById('portal-content');
        if (!container) return;

        const items = this.guestData[tabName] || [];

        if (!items.length) {
            let emptyMsg = 'No reservations found in this section.';
            let actionBtn = '';
            if (tabName === 'upcoming') {
                emptyMsg = 'You have no upcoming reservations.';
                actionBtn = '<button class="btn btn-primary" onclick="App.navigate(\'rooms\')" style="margin-top:12px">+ Book a Stay Now</button>';
            } else if (tabName === 'completed') {
                emptyMsg = 'You do not have any past completed stays yet.';
            } else if (tabName === 'cancelled') {
                emptyMsg = 'You have no cancelled reservations.';
            }

            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">${tabName === 'upcoming' ? '🧳' : tabName === 'completed' ? '🏆' : '📁'}</div>
                    <p class="empty-state-text">${emptyMsg}</p>
                    ${actionBtn}
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Reservation Reference</th>
                            <th>Hotel & Location</th>
                            <th>Room Details</th>
                            <th>Stay Dates</th>
                            <th>Nights</th>
                            <th>Total Price</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${items.map(r => {
                            const canCancel = Boolean(r.can_cancel) && ['Active', 'Confirmed'].includes(r.status);
                            return `
                                <tr>
                                    <td>
                                        <div style="display:flex;align-items:center;gap:6px">
                                            <span style="font-family:monospace;font-weight:800;color:var(--accent-blue);font-size:0.95rem">
                                                ${r.res_id}
                                            </span>
                                            <button type="button" class="btn btn-sm btn-secondary" style="padding:2px 6px;font-size:0.7rem"
                                                onclick="navigator.clipboard.writeText('${r.res_id}');App.toast('Copied ${r.res_id}','success')" title="Copy ID">
                                                📋
                                            </button>
                                        </div>
                                    </td>
                                    <td>
                                        <div style="font-weight:600">${r.hotel_name || '-'}</div>
                                        <div style="font-size:0.75rem;color:var(--text-muted)">📍 ${r.location || '-'}</div>
                                    </td>
                                    <td>
                                        <div style="font-weight:600">Room #${r.room_no}</div>
                                        <div style="font-size:0.75rem;color:var(--accent-purple)">${r.category || 'Standard'}</div>
                                    </td>
                                    <td>
                                        <div>${r.check_in_date || '-'} →</div>
                                        <div>${r.check_out_date || '-'}</div>
                                    </td>
                                    <td>${r.nights ? `${r.nights} night${r.nights > 1 ? 's' : ''}` : '-'}</td>
                                    <td>
                                        <span class="price-highlight">
                                            ${r.total_amount ? `₹${r.total_amount.toLocaleString()}` : (r.rent ? `₹${r.rent.toLocaleString()}/nt` : '-')}
                                        </span>
                                    </td>
                                    <td>${App.statusBadge(r.status)}</td>
                                    <td>
                                        ${canCancel ? `
                                            <button class="btn btn-sm btn-danger" onclick="ReservationsComponent.promptCancelGuest('${r.res_id}', ${r.room_no})">
                                                Cancel Booking
                                            </button>
                                        ` : `
                                            <span style="color:var(--text-muted);font-size:0.8rem">-</span>
                                        `}
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    promptCancelGuest(resId, roomNo) {
        const session = Auth.getSession();
        const body = `
            <div style="text-align:center;padding:12px">
                <div style="font-size:2.4rem;margin-bottom:12px">⚠️</div>
                <h3 style="font-size:1.15rem;font-weight:700;margin-bottom:8px">Cancel Reservation ${resId}?</h3>
                <p style="color:var(--text-secondary);font-size:0.88rem;margin-bottom:20px;line-height:1.5">
                    Are you sure you want to cancel your booking? Room #${roomNo} will be immediately made available for other guests.
                </p>
                <div style="display:flex;gap:12px">
                    <button class="btn btn-secondary" onclick="App.closeModal()" style="flex:1">Keep Booking</button>
                    <button class="btn btn-danger" onclick="ReservationsComponent.confirmCancelGuest('${resId}')" style="flex:1">
                        Confirm Cancellation
                    </button>
                </div>
            </div>
        `;
        App.showModal('Cancel Reservation', body);
    },

    async confirmCancelGuest(resId) {
        const session = Auth.getSession();
        try {
            await API.cancelReservation(resId, session.guest_id);
            App.closeModal();
            App.toast(`Reservation ${resId} cancelled. Room is now available.`, 'success');
            await this.loadGuestPortalData();
        } catch (err) {
            App.toast(err.message || 'Failed to cancel reservation', 'error');
        }
    },

    // =========================================================================
    // ADMIN / STAFF MANAGEMENT VIEW
    // =========================================================================
    async renderAdminView() {
        const content = document.getElementById('content-area');
        content.innerHTML = `
            <div class="action-bar" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px">
                <div>
                    <h2 style="font-size:1.35rem;font-weight:700">All Reservations</h2>
                    <p style="color:var(--text-secondary);font-size:0.85rem">Staff administration dashboard</p>
                </div>
                <button class="btn btn-primary" onclick="ReservationsComponent.showCreateForm()" id="btn-new-reservation">
                    + New Reservation
                </button>
            </div>
            <div class="card">
                <div id="reservations-table"><div class="loading-spinner"><div class="spinner"></div></div></div>
            </div>
        `;
        await this.loadAdminReservations();
    },

    async loadAdminReservations() {
        try {
            const reservations = await API.getReservations();
            this.allReservations = reservations;
            const el = document.getElementById('reservations-table');
            if (!reservations.length) {
                el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><p class="empty-state-text">No reservations found</p></div>';
                return;
            }
            el.innerHTML = `
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Guest</th>
                                <th>Room</th>
                                <th>Hotel</th>
                                <th>Category</th>
                                <th>Check In</th>
                                <th>Check Out</th>
                                <th>Staff</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${reservations.map(r => `
                                <tr>
                                    <td><strong>${r.res_id}</strong></td>
                                    <td>${r.guest_name} <span style="font-size:0.75rem;color:var(--text-muted)">(${r.guest_id || ''})</span></td>
                                    <td>${r.room_no}</td>
                                    <td>${r.hotel_name}</td>
                                    <td>${r.category || '-'}</td>
                                    <td>${r.check_in_date || '-'}</td>
                                    <td>${r.check_out_date || '-'}</td>
                                    <td>${r.staff_name || '-'}</td>
                                    <td>${App.statusBadge(r.status)}</td>
                                    <td>
                                        ${['Active', 'Confirmed'].includes(r.status) ?
                                            `<button class="btn btn-sm btn-danger" onclick="ReservationsComponent.adminCancel('${r.res_id}')">Cancel</button>` :
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

    async adminCancel(resId) {
        if (!confirm(`Cancel reservation ${resId}? This will free up the room.`)) return;
        try {
            await API.cancelReservation(resId);
            App.toast(`Reservation ${resId} cancelled`, 'success');
            await this.loadAdminReservations();
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

        const session = Auth.getSession();
        const activeGuestId = session ? session.guest_id : '';
        const today = new Date().toISOString().split('T')[0];
        const body = `
            <form id="create-res-form" onsubmit="ReservationsComponent.submitCreate(event)">
                <div class="form-group">
                    <label class="form-label" for="new-res-id">Reservation ID (leave blank to auto-generate)</label>
                    <input type="text" class="form-input" id="new-res-id" placeholder="e.g. R010 (optional)">
                </div>
                <div class="form-group">
                    <label class="form-label" for="new-res-guest">Guest</label>
                    <select class="form-select" id="new-res-guest" required>
                        <option value="">Select Guest</option>
                        ${guests.map(g => `<option value="${g.guest_id}" ${g.guest_id === activeGuestId ? 'selected' : ''}>${g.name} (${g.guest_id})${g.guest_id === activeGuestId ? ' - You' : ''}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label" for="new-res-room">Room (Available Only)</label>
                    <select class="form-select" id="new-res-room" required>
                        <option value="">Select Room</option>
                        ${rooms.map(r => `<option value="${r.room_no}">${r.room_no} — ${r.hotel_name} (${r.category}, ₹${r.rent})</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label" for="new-res-staff">Processing Staff</label>
                    <select class="form-select" id="new-res-staff">
                        <option value="S001">S001 — Front Desk (Default)</option>
                        ${staff.map(s => `<option value="${s.staff_id}">${s.name} — ${s.department}, ${s.hotel_name} (${s.staff_id})</option>`).join('')}
                    </select>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label" for="new-res-checkin">Check-In Date</label>
                        <input type="date" class="form-input" id="new-res-checkin" required min="${today}">
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="new-res-checkout">Check-Out Date</label>
                        <input type="date" class="form-input" id="new-res-checkout" required min="${today}">
                    </div>
                </div>
                <div id="res-form-error" class="form-error" style="margin-bottom:8px;color:var(--accent-red)"></div>
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
            errorEl.textContent = 'Check-out date must be strictly after check-in date.';
            return;
        }

        const rawResId = document.getElementById('new-res-id').value.trim();
        const data = {
            res_id: rawResId || undefined,
            guest_id: document.getElementById('new-res-guest').value,
            room_no: parseInt(document.getElementById('new-res-room').value),
            staff_id: document.getElementById('new-res-staff').value || 'S001',
            check_in_date: checkin,
            check_out_date: checkout,
        };

        try {
            const res = await API.createReservation(data);
            App.toast(`Reservation ${res.res_id} created!`, 'success');
            App.closeModal();
            await this.loadAdminReservations();
        } catch (e) {
            errorEl.textContent = e.message;
            App.toast(e.message, 'error');
        }
    }
};
