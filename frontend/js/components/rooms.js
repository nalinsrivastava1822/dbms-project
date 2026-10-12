/**
 * Rooms Component — Smart Room Availability Search, Filtering, and Booking.
 */
const RoomsComponent = {
    currentSearch: {
        hotel_id: '',
        location: '',
        category: '',
        max_rent: '',
        status: '',
        check_in: '',
        check_out: '',
        nights: 0,
    },
    loadedRooms: [],

    async render() {
        const isAdmin = Auth.isAdmin();
        const today = new Date().toISOString().split('T')[0];
        const tomorrowDate = new Date();
        tomorrowDate.setDate(tomorrowDate.getDate() + 1);
        const tomorrow = tomorrowDate.toISOString().split('T')[0];

        const content = document.getElementById('content-area');
        content.innerHTML = `
            <div class="action-bar" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px">
                <div>
                    <h2 style="font-size:1.3rem;font-weight:700">Smart Room Availability & Booking</h2>
                    <p style="color:var(--text-secondary);font-size:0.85rem">Search real-time availability across hotels, dates, and price tiers</p>
                </div>
                ${isAdmin ? '<button class="btn btn-primary" onclick="RoomsComponent.showAddForm()" id="btn-add-room">+ Add Room</button>' : ''}
            </div>

            <!-- Smart Room Search Bar -->
            <div class="card" style="margin-bottom:20px;padding:18px">
                <form id="smart-search-form" onsubmit="RoomsComponent.onSearchSubmit(event)">
                    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:14px;align-items:end">
                        <div class="form-group" style="margin-bottom:0">
                            <label class="form-label" for="search-hotel">Hotel</label>
                            <select class="form-select" id="search-hotel">
                                <option value="">All Hotels</option>
                            </select>
                        </div>
                        <div class="form-group" style="margin-bottom:0">
                            <label class="form-label" for="search-location">City / Location</label>
                            <input type="text" class="form-input" id="search-location" placeholder="e.g. Mumbai, Delhi">
                        </div>
                        <div class="form-group" style="margin-bottom:0">
                            <label class="form-label" for="search-checkin">Check-in Date</label>
                            <input type="date" class="form-input" id="search-checkin" min="${today}">
                        </div>
                        <div class="form-group" style="margin-bottom:0">
                            <label class="form-label" for="search-checkout">Check-out Date</label>
                            <input type="date" class="form-input" id="search-checkout" min="${tomorrow}">
                        </div>
                        <div class="form-group" style="margin-bottom:0">
                            <label class="form-label" for="search-category">Category</label>
                            <select class="form-select" id="search-category">
                                <option value="">All Categories</option>
                            </select>
                        </div>
                        <div class="form-group" style="margin-bottom:0">
                            <label class="form-label" for="search-rent">Max Nightly Price</label>
                            <input type="number" class="form-input" id="search-rent" placeholder="₹ Max Rent" min="100">
                        </div>
                        ${isAdmin ? `
                        <div class="form-group" style="margin-bottom:0">
                            <label class="form-label" for="search-status">Current Status</label>
                            <select class="form-select" id="search-status">
                                <option value="">All</option>
                                <option value="Available">Available</option>
                                <option value="Occupied">Occupied</option>
                                <option value="Maintenance">Maintenance</option>
                            </select>
                        </div>
                        ` : ''}
                        <div style="display:flex;gap:8px">
                            <button type="submit" class="btn btn-primary" id="btn-search-rooms" style="flex:1">🔍 Search</button>
                            <button type="button" class="btn btn-secondary" onclick="RoomsComponent.resetSearch()">Reset</button>
                        </div>
                    </div>
                </form>
            </div>

            <!-- Results container -->
            <div class="card">
                <div id="rooms-search-summary" style="margin-bottom:12px;font-size:0.88rem;color:var(--text-secondary);display:none"></div>
                <div id="rooms-table"><div class="loading-spinner"><div class="spinner"></div></div></div>
            </div>
        `;

        this.setupDateListeners();
        await this.loadFilters();
        await this.loadRooms();
    },

    setupDateListeners() {
        const checkin = document.getElementById('search-checkin');
        const checkout = document.getElementById('search-checkout');
        if (!checkin || !checkout) return;

        checkin.addEventListener('change', () => {
            if (checkin.value) {
                const nextDay = new Date(checkin.value);
                nextDay.setDate(nextDay.getDate() + 1);
                checkout.min = nextDay.toISOString().split('T')[0];
                if (checkout.value && checkout.value <= checkin.value) {
                    checkout.value = checkout.min;
                }
            }
        });
    },

    async loadFilters() {
        try {
            const [hotels, categories] = await Promise.all([API.getHotels(), API.getCategories()]);
            const hotelSelect = document.getElementById('search-hotel');
            if (hotelSelect) {
                hotels.forEach(h => {
                    const opt = document.createElement('option');
                    opt.value = h.hotel_id;
                    opt.textContent = `${h.name} (${h.location || 'Location'})`;
                    hotelSelect.appendChild(opt);
                });
            }
            const catSelect = document.getElementById('search-category');
            if (catSelect) {
                categories.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.category_name;
                    opt.textContent = `${c.category_name} (₹${c.rent}/night)`;
                    catSelect.appendChild(opt);
                });
            }
        } catch (e) {
            console.warn('Failed to load room filters:', e);
        }
    },

    async loadRooms() {
        try {
            const rooms = await API.getRooms();
            this.loadedRooms = rooms;
            this.currentSearch.check_in = '';
            this.currentSearch.check_out = '';
            this.currentSearch.nights = 0;
            this.renderTable(rooms);
        } catch (e) {
            document.getElementById('rooms-table').innerHTML = `<p class="empty-state-text">⚠️ ${e.message}</p>`;
        }
    },

    onSearchSubmit(e) {
        e.preventDefault();
        this.search();
    },

    resetSearch() {
        const form = document.getElementById('smart-search-form');
        if (form) form.reset();
        const summary = document.getElementById('rooms-search-summary');
        if (summary) summary.style.display = 'none';
        this.loadRooms();
    },

    async search() {
        const checkin = document.getElementById('search-checkin')?.value || '';
        const checkout = document.getElementById('search-checkout')?.value || '';
        const hotelId = document.getElementById('search-hotel')?.value || '';
        const location = document.getElementById('search-location')?.value.trim() || '';
        const category = document.getElementById('search-category')?.value || '';
        const rent = document.getElementById('search-rent')?.value || '';
        const status = document.getElementById('search-status')?.value || '';

        // Validate dates if either is provided
        if ((checkin && !checkout) || (!checkin && checkout)) {
            App.toast('Please provide both Check-in and Check-out dates to search by date availability.', 'error');
            return;
        }

        if (checkin && checkout) {
            if (checkout <= checkin) {
                App.toast('Check-out date must be strictly after check-in date.', 'error');
                return;
            }
        }

        let nights = 0;
        if (checkin && checkout) {
            const dIn = new Date(checkin);
            const dOut = new Date(checkout);
            nights = Math.max(1, Math.round((dOut - dIn) / (1000 * 60 * 60 * 24)));
        }

        this.currentSearch = {
            hotel_id: hotelId,
            location: location,
            category: category,
            max_rent: rent,
            status: status,
            check_in: checkin,
            check_out: checkout,
            nights: nights,
        };

        const params = {
            hotel_id: hotelId || undefined,
            location: location || undefined,
            category: category || undefined,
            max_rent: rent || undefined,
            status: status || undefined,
            check_in: checkin || undefined,
            check_out: checkout || undefined,
        };

        const tableEl = document.getElementById('rooms-table');
        tableEl.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';

        try {
            const rooms = await API.searchRooms(params);
            this.loadedRooms = rooms;
            this.renderTable(rooms);

            const summaryEl = document.getElementById('rooms-search-summary');
            if (summaryEl) {
                summaryEl.style.display = 'block';
                if (checkin && checkout) {
                    summaryEl.innerHTML = `📅 Showing available rooms for <strong>${checkin}</strong> to <strong>${checkout}</strong> (${nights} night${nights > 1 ? 's' : ''}) · <strong>${rooms.length}</strong> available`;
                } else {
                    summaryEl.innerHTML = `Showing <strong>${rooms.length}</strong> matching rooms`;
                }
            }
            App.toast(`Found ${rooms.length} available room${rooms.length === 1 ? '' : 's'}`, 'info');
        } catch (e) {
            tableEl.innerHTML = `<p class="empty-state-text">⚠️ ${e.message}</p>`;
            App.toast(e.message, 'error');
        }
    },

    renderTable(rooms) {
        const el = document.getElementById('rooms-table');
        if (!rooms || !rooms.length) {
            el.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🛏️</div>
                    <p class="empty-state-text" style="font-weight:600">No rooms match your availability criteria</p>
                    <p style="color:var(--text-muted);font-size:0.85rem">Try different dates, increasing maximum nightly price, or removing category filters.</p>
                </div>
            `;
            return;
        }

        const hasDates = Boolean(this.currentSearch.check_in && this.currentSearch.check_out);
        const isAdmin = Auth.isAdmin();

        el.innerHTML = `
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Room</th>
                            <th>Hotel</th>
                            <th>Location</th>
                            <th>Category</th>
                            <th>Nightly Rent</th>
                            ${hasDates ? '<th>Duration</th><th>Estimated Total</th>' : ''}
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rooms.map(r => {
                            const nights = r.nights || this.currentSearch.nights || 1;
                            const totalEst = r.estimated_total_price || (r.rent ? r.rent * nights : 0);
                            return `
                                <tr>
                                    <td><strong>#${r.room_no}</strong></td>
                                    <td>${r.hotel_name || '-'}</td>
                                    <td><span style="color:var(--accent-blue)">📍 ${r.location || '-'}</span></td>
                                    <td><span class="badge" style="background:rgba(139,92,246,0.15);color:#a78bfa">${r.category || '-'}</span></td>
                                    <td><strong>₹${(r.rent || 0).toLocaleString()}</strong><span style="font-size:0.75rem;color:var(--text-muted)">/night</span></td>
                                    ${hasDates ? `
                                        <td>${nights} night${nights > 1 ? 's' : ''}</td>
                                        <td><span class="price-highlight">₹${totalEst.toLocaleString()}</span></td>
                                    ` : ''}
                                    <td>${App.statusBadge(r.status)}</td>
                                    <td>
                                        <div style="display:flex;align-items:center;gap:6px">
                                            <button class="btn btn-sm btn-primary" onclick="RoomsComponent.openBookModal(${r.room_no})" style="white-space:nowrap">
                                                Book Room
                                            </button>
                                            ${isAdmin ? `
                                                <select class="form-select" style="width:auto;padding:4px 28px 4px 8px;font-size:0.78rem"
                                                    onchange="RoomsComponent.updateStatus(${r.room_no}, this.value)">
                                                    <option value="" disabled selected>Status</option>
                                                    <option value="Available">Available</option>
                                                    <option value="Occupied">Occupied</option>
                                                    <option value="Maintenance">Maintenance</option>
                                                </select>
                                            ` : ''}
                                        </div>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    async updateStatus(roomNo, status) {
        try {
            await API.updateRoomStatus(roomNo, status);
            App.toast(`Room ${roomNo} status updated to ${status}`, 'success');
            if (this.currentSearch.check_in && this.currentSearch.check_out) {
                this.search();
            } else {
                this.loadRooms();
            }
        } catch (e) {
            App.toast(e.message, 'error');
        }
    },

    async openBookModal(roomNo) {
        const room = this.loadedRooms.find(r => r.room_no === roomNo) || { room_no: roomNo };
        const session = Auth.getSession();
        const isGuest = Auth.isGuest();
        const isAdmin = Auth.isAdmin();

        const today = new Date().toISOString().split('T')[0];
        const tomorrowDate = new Date();
        tomorrowDate.setDate(tomorrowDate.getDate() + 1);
        const tomorrow = tomorrowDate.toISOString().split('T')[0];

        let defaultCheckin = this.currentSearch.check_in || today;
        let defaultCheckout = this.currentSearch.check_out || tomorrow;

        let guests = [];
        if (isAdmin) {
            try {
                guests = await API.getGuests();
            } catch (e) {
                console.warn('Failed to load guests for booking form:', e);
            }
        }

        const nightlyRate = room.rent || 3000;
        const dIn = new Date(defaultCheckin);
        const dOut = new Date(defaultCheckout);
        const nights = Math.max(1, Math.round((dOut - dIn) / (1000 * 60 * 60 * 24)));
        const total = nightlyRate * nights;

        const body = `
            <div class="booking-confirm-card" style="margin-bottom:16px">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
                    <div>
                        <h3 style="font-size:1.15rem;font-weight:700;margin-bottom:2px">Room #${room.room_no} — ${room.category || 'Standard'}</h3>
                        <p style="color:var(--text-secondary);font-size:0.85rem">🏨 ${room.hotel_name || 'Selected Hotel'} · 📍 ${room.location || 'Location'}</p>
                    </div>
                    <div style="text-align:right">
                        <span style="font-size:0.8rem;color:var(--text-muted)">Nightly Rate</span>
                        <div style="font-size:1.1rem;font-weight:700;color:var(--accent-blue)">₹${nightlyRate.toLocaleString()}<span style="font-size:0.75rem">/night</span></div>
                    </div>
                </div>

                <form id="book-room-form" onsubmit="RoomsComponent.submitBooking(event, ${room.room_no}, ${nightlyRate})">
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label" for="book-checkin">Check-in Date</label>
                            <input type="date" class="form-input" id="book-checkin" required min="${today}" value="${defaultCheckin}">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="book-checkout">Check-out Date</label>
                            <input type="date" class="form-input" id="book-checkout" required min="${defaultCheckin || today}" value="${defaultCheckout}">
                        </div>
                    </div>

                    ${isGuest ? `
                        <div class="form-group">
                            <label class="form-label">Guest Information</label>
                            <div class="summary-item" style="display:flex;justify-content:space-between;align-items:center">
                                <div>
                                    <div style="font-weight:600">👤 ${session.displayName || 'Guest'}</div>
                                    <div style="font-size:0.75rem;color:var(--text-muted)">Guest ID: ${session.guest_id}</div>
                                </div>
                                <span class="badge badge-active">Authenticated Guest</span>
                            </div>
                            <input type="hidden" id="book-guest-id" value="${session.guest_id}">
                        </div>
                    ` : `
                        <div class="form-group">
                            <label class="form-label" for="book-guest-id">Select Guest</label>
                            <select class="form-select" id="book-guest-id" required>
                                <option value="">Select a guest...</option>
                                ${guests.map(g => `<option value="${g.guest_id}">${g.name} (${g.guest_id})</option>`).join('')}
                            </select>
                        </div>
                    `}

                    <div class="summary-grid" style="margin-top:14px">
                        <div class="summary-item">
                            <div class="summary-label">Duration</div>
                            <div class="summary-val" id="book-nights-display">${nights} Night${nights > 1 ? 's' : ''}</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Estimated Total</div>
                            <div class="summary-val price-highlight" id="book-total-display">₹${total.toLocaleString()}</div>
                        </div>
                    </div>

                    <div id="book-error" class="form-error" style="margin-bottom:12px;color:var(--accent-red);font-size:0.85rem"></div>

                    <div style="display:flex;gap:10px;margin-top:10px">
                        <button type="button" class="btn btn-secondary" onclick="App.closeModal()" style="flex:1">Cancel</button>
                        <button type="submit" class="btn btn-primary" id="btn-confirm-book" style="flex:2">
                            ✓ Confirm Reservation
                        </button>
                    </div>
                </form>
            </div>
        `;

        App.showModal('Reserve Room', body);

        // Recalculate price dynamically when dates change in modal
        const checkinInput = document.getElementById('book-checkin');
        const checkoutInput = document.getElementById('book-checkout');
        const nightsDisplay = document.getElementById('book-nights-display');
        const totalDisplay = document.getElementById('book-total-display');

        function updateModalPrice() {
            const inVal = checkinInput.value;
            const outVal = checkoutInput.value;
            if (inVal && outVal && outVal > inVal) {
                const diff = Math.max(1, Math.round((new Date(outVal) - new Date(inVal)) / (1000 * 60 * 60 * 24)));
                nightsDisplay.textContent = `${diff} Night${diff > 1 ? 's' : ''}`;
                totalDisplay.textContent = `₹${(nightlyRate * diff).toLocaleString()}`;
            }
        }

        checkinInput.addEventListener('change', () => {
            if (checkinInput.value) {
                const nxt = new Date(checkinInput.value);
                nxt.setDate(nxt.getDate() + 1);
                checkoutInput.min = nxt.toISOString().split('T')[0];
                if (checkoutInput.value && checkoutInput.value <= checkinInput.value) {
                    checkoutInput.value = checkoutInput.min;
                }
            }
            updateModalPrice();
        });
        checkoutInput.addEventListener('change', updateModalPrice);
    },

    async submitBooking(e, roomNo, rent) {
        e.preventDefault();
        const errorEl = document.getElementById('book-error');
        errorEl.textContent = '';

        const checkin = document.getElementById('book-checkin').value;
        const checkout = document.getElementById('book-checkout').value;
        const guestId = document.getElementById('book-guest-id').value;

        if (!checkin || !checkout) {
            errorEl.textContent = 'Please choose both check-in and check-out dates.';
            return;
        }

        if (checkout <= checkin) {
            errorEl.textContent = 'Check-out date must be strictly after check-in date.';
            return;
        }

        if (!guestId) {
            errorEl.textContent = 'A guest must be selected to complete the reservation.';
            return;
        }

        const dIn = new Date(checkin);
        const dOut = new Date(checkout);
        const nights = Math.max(1, Math.round((dOut - dIn) / (1000 * 60 * 60 * 24)));
        const totalAmount = rent * nights;

        const btn = document.getElementById('btn-confirm-book');
        btn.disabled = true;
        btn.textContent = 'Securing Reservation in Neo4j…';

        try {
            const reservationData = {
                guest_id: guestId,
                room_no: roomNo,
                check_in_date: checkin,
                check_out_date: checkout,
                total_amount: totalAmount,
                staff_id: 'S001',
            };

            const result = await API.createReservation(reservationData);
            App.closeModal();

            const room = this.loadedRooms.find(r => r.room_no === roomNo) || { room_no: roomNo };
            this.showBookingConfirmation(result, room, {
                check_in: checkin,
                check_out: checkout,
                nights: nights,
                total: totalAmount,
            });

            // Refresh search so room disappears if requested dates overlap
            if (this.currentSearch.check_in && this.currentSearch.check_out) {
                this.search();
            }
        } catch (err) {
            errorEl.textContent = err.message || 'Database error while reserving room';
            btn.disabled = false;
            btn.textContent = '✓ Confirm Reservation';
            App.toast(err.message, 'error');
        }
    },

    showBookingConfirmation(res, room, details) {
        const resId = res.res_id || 'CONFIRMED';
        const body = `
            <div class="booking-confirm-card" style="text-align:center">
                <span class="confirm-icon">🎉</span>
                <h3 style="font-size:1.35rem;font-weight:700;margin-bottom:4px">Booking Confirmed!</h3>
                <p style="color:var(--text-secondary);font-size:0.88rem">
                    Your reservation has been atomically committed to Neo4j.
                </p>

                <div class="res-ref-box">
                    <div>
                        <div style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px">
                            Unique Reservation Reference
                        </div>
                        <div class="res-ref-number" id="confirmed-res-id">${resId}</div>
                    </div>
                    <button type="button" class="copy-badge-btn" onclick="navigator.clipboard.writeText('${resId}');App.toast('Copied ${resId} to clipboard!','success')">
                        📋 Copy
                    </button>
                </div>

                <div class="summary-grid" style="text-align:left">
                    <div class="summary-item">
                        <div class="summary-label">Hotel & Location</div>
                        <div class="summary-val">${room.hotel_name || res.hotel_name || 'Hotel'} (${room.location || res.location || 'Location'})</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Room Reserved</div>
                        <div class="summary-val">Room #${room.room_no || res.room_no} (${room.category || 'Standard'})</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Stay Dates</div>
                        <div class="summary-val">${details.check_in} → ${details.check_out}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Total Amount</div>
                        <div class="summary-val price-highlight">₹${details.total.toLocaleString()} (${details.nights} night${details.nights > 1 ? 's' : ''})</div>
                    </div>
                </div>

                <div style="display:flex;gap:10px;margin-top:20px">
                    <button class="btn btn-secondary" onclick="App.closeModal();RoomsComponent.search()" style="flex:1">
                        Search More Rooms
                    </button>
                    <button class="btn btn-primary" onclick="App.closeModal();App.navigate('reservations')" style="flex:1">
                        📋 View in My Reservations
                    </button>
                </div>
            </div>
        `;

        App.showModal('Reservation Confirmation', body);
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
