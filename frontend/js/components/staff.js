/**
 * Staff Component — List staff by department, view reservation processing.
 */
const StaffComponent = {
    async render() {
        const content = document.getElementById('content-area');
        content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading staff...</p></div>';

        try {
            const departments = await API.getStaffByDepartment();
            if (!departments.length) {
                content.innerHTML = '<div class="empty-state"><div class="empty-state-icon">👥</div><p class="empty-state-text">No staff data</p></div>';
                return;
            }

            content.innerHTML = departments.map(dept => `
                <div class="card" style="margin-bottom:20px">
                    <div class="card-header">
                        <div>
                            <h3 class="card-title">${dept.department} Department</h3>
                            <p class="card-subtitle">${dept.hotel_name} · Head: ${dept.dept_head} · ID: ${dept.dept_id}</p>
                        </div>
                        <span class="badge badge-active">${dept.staff.length} staff</span>
                    </div>
                    <div class="table-wrapper">
                        <table>
                            <thead><tr>
                                <th>ID</th><th>Name</th><th>Age</th><th>Salary</th><th>Contact</th><th>Action</th>
                            </tr></thead>
                            <tbody>
                                ${dept.staff.map(s => `
                                    <tr>
                                        <td>${s.staff_id}</td>
                                        <td><strong>${s.name}</strong></td>
                                        <td>${s.age}</td>
                                        <td>₹${s.salary?.toLocaleString()}</td>
                                        <td>${s.contact_info}</td>
                                        <td><button class="btn btn-sm btn-secondary" onclick="StaffComponent.showReservations('${s.staff_id}')">Reservations</button></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            content.innerHTML = `<div class="empty-state"><p class="empty-state-text">⚠️ ${e.message}</p></div>`;
        }
    },

    async showReservations(staffId) {
        try {
            const data = await API.getStaffReservations(staffId);
            const body = `
                <p style="color:var(--text-secondary);margin-bottom:16px">Staff: <strong>${data.staff_name}</strong> (${data.staff_id})</p>
                ${data.reservations.length ? `
                    <div class="table-wrapper">
                        <table>
                            <thead><tr><th>Res ID</th><th>Guest</th><th>Room</th><th>Hotel</th><th>Check In</th><th>Status</th></tr></thead>
                            <tbody>
                                ${data.reservations.map(r => `
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
                ` : '<div class="empty-state"><p class="empty-state-text">No reservations processed by this staff member</p></div>'}
            `;
            App.showModal(`Reservations Processed`, body);
        } catch (e) {
            App.toast(e.message, 'error');
        }
    }
};
