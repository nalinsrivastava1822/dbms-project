/**
 * Recommendations Component — Graph-specific traversal features.
 */
const RecommendationsComponent = {
    async render() {
        const content = document.getElementById('content-area');

        let guests;
        try {
            guests = await API.getGuests();
        } catch (e) {
            content.innerHTML = `<div class="empty-state"><p class="empty-state-text">⚠️ ${e.message}</p></div>`;
            return;
        }

        content.innerHTML = `
            <div class="rec-explanation">
                <strong>Graph-Powered Recommendations</strong><br>
                These features use Neo4j's multi-hop Cypher traversals to discover patterns that would
                require complex self-joins in SQL. The graph model naturally represents relationships between
                guests, reservations, rooms, and hotels — making traversal queries concise and efficient.
                <br><br>
                <em>Note: Neo4j excels at relationship-heavy queries but is not universally superior to relational
                databases. For structured tabular data and strict ACID transactions, SQL databases remain strong choices.</em>
            </div>

            <div class="section-grid">
                <!-- Hotel Recommendations -->
                <div class="card">
                    <div class="card-header">
                        <div><h3 class="card-title">🏨 Hotel Recommendations</h3>
                        <p class="card-subtitle">Based on similar guests' stays</p></div>
                    </div>
                    <div class="form-group">
                        <select class="form-select" id="rec-hotel-guest">
                            <option value="">Select a guest</option>
                            ${guests.map(g => `<option value="${g.guest_id}">${g.name} (${g.guest_id})</option>`).join('')}
                        </select>
                    </div>
                    <button class="btn btn-primary btn-sm" onclick="RecommendationsComponent.getHotelRecs()">Get Recommendations</button>
                    <div id="rec-hotel-results" style="margin-top:16px"></div>
                </div>

                <!-- Room Category Recommendations -->
                <div class="card">
                    <div class="card-header">
                        <div><h3 class="card-title">🛏️ Room Category Suggestions</h3>
                        <p class="card-subtitle">Based on past preferences</p></div>
                    </div>
                    <div class="form-group">
                        <select class="form-select" id="rec-room-guest">
                            <option value="">Select a guest</option>
                            ${guests.map(g => `<option value="${g.guest_id}">${g.name} (${g.guest_id})</option>`).join('')}
                        </select>
                    </div>
                    <button class="btn btn-primary btn-sm" onclick="RecommendationsComponent.getRoomRecs()">Get Suggestions</button>
                    <div id="rec-room-results" style="margin-top:16px"></div>
                </div>

                <!-- Popular by Nationality -->
                <div class="card">
                    <div class="card-header">
                        <div><h3 class="card-title">🌍 Popular Hotels by Nationality</h3>
                        <p class="card-subtitle">Where compatriots stay</p></div>
                    </div>
                    <div class="form-group">
                        <input type="text" class="form-input" id="rec-nationality" placeholder="e.g. Indian">
                    </div>
                    <button class="btn btn-primary btn-sm" onclick="RecommendationsComponent.getNatRecs()">Search</button>
                    <div id="rec-nat-results" style="margin-top:16px"></div>
                </div>

                <!-- Guest Journey -->
                <div class="card">
                    <div class="card-header">
                        <div><h3 class="card-title">🗺️ Guest Journey Map</h3>
                        <p class="card-subtitle">Full traversal across all entities</p></div>
                    </div>
                    <div class="form-group">
                        <select class="form-select" id="rec-journey-guest">
                            <option value="">Select a guest</option>
                            ${guests.map(g => `<option value="${g.guest_id}">${g.name} (${g.guest_id})</option>`).join('')}
                        </select>
                    </div>
                    <button class="btn btn-primary btn-sm" onclick="RecommendationsComponent.getJourney()">Trace Journey</button>
                    <div id="rec-journey-results" style="margin-top:16px"></div>
                </div>
            </div>
        `;
    },

    async getHotelRecs() {
        const guestId = document.getElementById('rec-hotel-guest').value;
        if (!guestId) { App.toast('Select a guest', 'error'); return; }
        const el = document.getElementById('rec-hotel-results');
        el.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';

        try {
            const data = await API.recommendHotels(guestId);
            if (!data.recommendations.length) {
                el.innerHTML = '<p class="empty-state-text">No recommendations found — this guest may have visited all available hotels, or there are no overlapping guests.</p>';
                return;
            }
            el.innerHTML = data.recommendations.map(r => `
                <div class="rec-card">
                    <div class="rec-title">${r.hotel_name}</div>
                    <div class="rec-meta">
                        📍 ${r.location} · ${'★'.repeat(Math.round(r.rating))} ${r.rating}<br>
                        👥 ${r.shared_guests} shared guest(s): ${r.guests_who_stayed.join(', ')}
                    </div>
                </div>
            `).join('');
        } catch (e) {
            el.innerHTML = `<p class="empty-state-text">⚠️ ${e.message}</p>`;
        }
    },

    async getRoomRecs() {
        const guestId = document.getElementById('rec-room-guest').value;
        if (!guestId) { App.toast('Select a guest', 'error'); return; }
        const el = document.getElementById('rec-room-results');
        el.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';

        try {
            const data = await API.recommendRooms(guestId);
            if (!data.recommendations.length) {
                el.innerHTML = '<p class="empty-state-text">This guest has tried all categories, or has no booking history.</p>';
                return;
            }
            el.innerHTML = data.recommendations.map(r => `
                <div class="rec-card">
                    <div class="rec-title">${r.category}</div>
                    <div class="rec-meta">₹${r.rent?.toLocaleString()} / night · Price diff: ₹${r.price_difference?.toLocaleString()}</div>
                </div>
            `).join('');
        } catch (e) {
            el.innerHTML = `<p class="empty-state-text">⚠️ ${e.message}</p>`;
        }
    },

    async getNatRecs() {
        const nat = document.getElementById('rec-nationality').value.trim();
        if (!nat) { App.toast('Enter a nationality', 'error'); return; }
        const el = document.getElementById('rec-nat-results');
        el.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';

        try {
            const data = await API.popularByNationality(nat);
            if (!data.popular_hotels.length) {
                el.innerHTML = `<p class="empty-state-text">No bookings found for ${nat} guests.</p>`;
                return;
            }
            el.innerHTML = data.popular_hotels.map(r => `
                <div class="rec-card">
                    <div class="rec-title">${r.hotel_name}</div>
                    <div class="rec-meta">
                        📍 ${r.location} · ${'★'.repeat(Math.round(r.rating))} ${r.rating}<br>
                        👥 ${r.guests_from_country} guest(s) · 📋 ${r.total_bookings} booking(s)
                    </div>
                </div>
            `).join('');
        } catch (e) {
            el.innerHTML = `<p class="empty-state-text">⚠️ ${e.message}</p>`;
        }
    },

    async getJourney() {
        const guestId = document.getElementById('rec-journey-guest').value;
        if (!guestId) { App.toast('Select a guest', 'error'); return; }
        const el = document.getElementById('rec-journey-results');
        el.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';

        try {
            const data = await API.guestJourney(guestId);
            if (!data.journey.length) {
                el.innerHTML = '<p class="empty-state-text">No journey data for this guest.</p>';
                return;
            }
            el.innerHTML = `
                <p style="font-size:0.82rem;color:var(--text-muted);margin-bottom:12px">${data.explanation}</p>
                ${data.journey.map((j, i) => `
                    <div class="rec-card">
                        <div class="rec-title">${i + 1}. ${j.hotel} — Room ${j.room}</div>
                        <div class="rec-meta">
                            ${j.category} · ₹${j.rent} · ${App.statusBadgeHTML(j.status)}<br>
                            📅 ${j.check_in} → ${j.check_out}<br>
                            👤 Processed by: ${j.processed_by || 'N/A'} ${j.staff_department ? `(${j.staff_department})` : ''}
                        </div>
                    </div>
                `).join('')}
            `;
        } catch (e) {
            el.innerHTML = `<p class="empty-state-text">⚠️ ${e.message}</p>`;
        }
    }
};
