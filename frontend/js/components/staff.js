/**
 * Staff Component — List staff by department, view reservation processing.
 */
const StaffComponent = {
    async render() {
        const content = document.getElementById('content-area');
        content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading staff...</p></div>';

        try {
            let data = await API.getStaffByDepartment();
            const headerHtml = `
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                    <div>
                        <h2 style="font-size:1.4rem;font-weight:700;">Staff Management</h2>
                        <p style="color:var(--text-secondary);font-size:0.85rem;">Manage hotel staff across departments and track reservation processing</p>
                    </div>
                    <button class="btn btn-primary" onclick="StaffComponent.showAddStaffModal()">➕ Add Staff</button>
                </div>
            `;

            if (!Array.isArray(data) || !data.length) {
                content.innerHTML = headerHtml + '<div class="empty-state"><div class="empty-state-icon">👥</div><p class="empty-state-text">No staff data</p></div>';
                return;
            }

            // Normalization: Support either grouped departments (dept.staff) or flat staff objects (s.staff_id)
            let departments = [];
            if (data[0] && Array.isArray(data[0].staff)) {
                departments = data;
            } else if (data[0] && data[0].staff_id) {
                // Group flat staff records by department
                const deptMap = {};
                data.forEach(s => {
                    const dId = s.dept_id || 'General';
                    if (!deptMap[dId]) {
                        deptMap[dId] = {
                            dept_id: dId,
                            department: s.department || s.d_role || dId,
                            dept_head: s.dept_head || 'Department Head',
                            hotel_name: s.hotel_name || 'Hotel Branch',
                            staff: []
                        };
                    }
                    deptMap[dId].staff.push(s);
                });
                departments = Object.values(deptMap);
            } else {
                departments = data;
            }

            content.innerHTML = headerHtml + departments.map(dept => {
                const staffList = Array.isArray(dept.staff) ? dept.staff : [];
                return `
                <div class="card" style="margin-bottom:20px">
                    <div class="card-header">
                        <div>
                            <h3 class="card-title">${dept.department || 'Department'}</h3>
                            <p class="card-subtitle">${dept.hotel_name || ''} · Head: ${dept.dept_head || 'N/A'} · ID: ${dept.dept_id || ''}</p>
                        </div>
                        <span class="badge badge-active">${staffList.length} staff</span>
                    </div>
                    <div class="table-wrapper">
                        <table>
                            <thead><tr>
                                <th>ID</th><th>Name</th><th>Age</th><th>Salary</th><th>Contact</th><th>Action</th>
                            </tr></thead>
                            <tbody>
                                ${staffList.map(s => `
                                    <tr>
                                        <td>${s.staff_id}</td>
                                        <td><strong>${s.name}</strong></td>
                                        <td>${s.age}</td>
                                        <td>₹${s.salary ? Number(s.salary).toLocaleString() : '0'}</td>
                                        <td>${s.contact_info || '-'}</td>
                                        <td><button class="btn btn-sm btn-secondary" onclick="StaffComponent.showReservations('${s.staff_id}')">Reservations</button></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `}).join('');
        } catch (e) {
            content.innerHTML = `<div class="empty-state"><p class="empty-state-text">⚠️ ${e.message}</p></div>`;
        }
    },

    showAddStaffModal() {
        const body = `
            <form id="add-staff-form" onsubmit="StaffComponent.handleAddStaff(event)">
                <div class="form-group" style="margin-bottom:12px">
                    <label style="font-size:0.85rem;color:var(--text-secondary)">Staff ID *</label>
                    <input type="text" id="staff-id" class="form-control" required placeholder="e.g. S007" style="width:100%;padding:8px;border-radius:6px;background:var(--bg-input);color:#fff;border:1px solid var(--border-color)">
                </div>
                <div class="form-group" style="margin-bottom:12px">
                    <label style="font-size:0.85rem;color:var(--text-secondary)">Full Name *</label>
                    <input type="text" id="staff-name" class="form-control" required placeholder="e.g. Ananya Sen" style="width:100%;padding:8px;border-radius:6px;background:var(--bg-input);color:#fff;border:1px solid var(--border-color)">
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
                    <div class="form-group">
                        <label style="font-size:0.85rem;color:var(--text-secondary)">Age *</label>
                        <input type="number" id="staff-age" class="form-control" required min="18" max="75" placeholder="e.g. 29" style="width:100%;padding:8px;border-radius:6px;background:var(--bg-input);color:#fff;border:1px solid var(--border-color)">
                    </div>
                    <div class="form-group">
                        <label style="font-size:0.85rem;color:var(--text-secondary)">Monthly Salary (₹) *</label>
                        <input type="number" id="staff-salary" class="form-control" required min="1000" step="500" placeholder="e.g. 35000" style="width:100%;padding:8px;border-radius:6px;background:var(--bg-input);color:#fff;border:1px solid var(--border-color)">
                    </div>
                </div>
                <div class="form-group" style="margin-bottom:12px">
                    <label style="font-size:0.85rem;color:var(--text-secondary)">Contact Info (Phone) *</label>
                    <input type="text" id="staff-contact" class="form-control" required placeholder="e.g. 9876543215" style="width:100%;padding:8px;border-radius:6px;background:var(--bg-input);color:#fff;border:1px solid var(--border-color)">
                </div>
                <div class="form-group" style="margin-bottom:16px">
                    <label style="font-size:0.85rem;color:var(--text-secondary)">Department *</label>
                    <select id="staff-dept" class="form-control" required style="width:100%;padding:8px;border-radius:6px;background:var(--bg-input);color:#fff;border:1px solid var(--border-color)">
                        <option value="D001">D001 — Front Desk (Grand Palace)</option>
                        <option value="D002">D002 — Housekeeping (Grand Palace)</option>
                        <option value="D003">D003 — Front Desk (Royal Orchid)</option>
                        <option value="D004">D004 — Restaurant (Royal Orchid)</option>
                        <option value="D005">D005 — Front Desk (Seaside Inn)</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%">Create Staff Member</button>
            </form>
        `;
        App.showModal('➕ Add New Staff Member', body);
    },

    async handleAddStaff(event) {
        event.preventDefault();
        try {
            const data = {
                staff_id: document.getElementById('staff-id').value.trim(),
                name: document.getElementById('staff-name').value.trim(),
                age: parseInt(document.getElementById('staff-age').value),
                salary: parseFloat(document.getElementById('staff-salary').value),
                contact_info: document.getElementById('staff-contact').value.trim(),
                dept_id: document.getElementById('staff-dept').value,
            };
            await API.createStaff(data);
            App.closeModal();
            App.toast(`Staff member ${data.name} (${data.staff_id}) added successfully!`, 'success');
            StaffComponent.render();
        } catch (e) {
            App.toast(e.message, 'error');
        }
    },

    async showReservations(staffId) {
        try {
            const data = await API.getStaffReservations(staffId);
            const body = `
                <p style="color:var(--text-secondary);margin-bottom:16px">Staff: <strong>${data.staff_name || 'Staff'}</strong> (${data.staff_id || staffId})</p>
                ${(data.reservations && data.reservations.length) ? `
                    <div class="table-wrapper">
                        <table>
                            <thead><tr><th>Res ID</th><th>Guest</th><th>Room</th><th>Hotel</th><th>Check In</th><th>Status</th></tr></thead>
                            <tbody>
                                ${(data.reservations || []).map(r => `
                                    <tr>
                                        <td>${r.res_id}</td>
                                        <td>${r.guest_name || 'Guest'}</td>
                                        <td>${r.room_no || '-'}</td>
                                        <td>${r.hotel_name || 'Hotel'}</td>
                                        <td>${r.check_in_date || r.check_in || '-'}</td>
                                        <td>${App.statusBadge(r.status)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                ` : '<div class="empty-state"><p class="empty-state-text">No reservations processed by this staff member</p></div>'}
            `;
            App.showModal(`Reservations Processed`, body);
        } catch (e) {
            App.toast(e.message, 'error');
        }
    }
};
