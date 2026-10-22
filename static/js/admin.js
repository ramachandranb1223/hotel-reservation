/**
 * Grand Luxe Hotel - Admin Management Portal JavaScript
 */

// Helper to format currency
const fmt = (num) => `$${Number(num || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

// -----------------------------------------------------------------------------
// DASHBOARD KPI INITIALIZATION
// -----------------------------------------------------------------------------
async function initAdminDashboard() {
    try {
        const resp = await apiRequest('/api/admin/dashboard');
        const s = resp.summary;
        
        // Rooms
        document.getElementById('kpi-total-rooms').textContent = s.rooms.total_rooms || 0;
        document.getElementById('kpi-available-rooms').textContent = s.rooms.available_rooms || 0;
        document.getElementById('kpi-occupied-rooms').textContent = s.rooms.occupied_rooms || 0;
        
        // Bookings & Revenue
        document.getElementById('kpi-total-revenue').textContent = fmt(s.total_collected);
        document.getElementById('kpi-total-bookings').textContent = s.bookings.total_bookings || 0;
        document.getElementById('kpi-active-stays').textContent = s.bookings.active_stays || 0;
        document.getElementById('kpi-total-customers').textContent = s.total_customers || 0;

        // Render Recent Bookings Table
        renderRecentBookings(resp.recent_bookings);
    } catch (err) {
        showToast(`Failed to load dashboard metrics: ${err.message}`, 'error');
    }
}

function renderRecentBookings(bookings) {
    const tbody = document.getElementById('recent-bookings-tbody');
    if (!tbody) return;

    if (!bookings || bookings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--color-text-muted);">No bookings found.</td></tr>`;
        return;
    }

    let html = '';
    bookings.forEach(b => {
        const bid = b.booking_id || b.Booking_ID;
        const name = b.customer_name || b.Customer_Name;
        const roomNum = b.room_number || b.Room_Number;
        const checkIn = b.check_in_date || b.Check_In_Date;
        const checkOut = b.check_out_date || b.Check_Out_Date;
        const total = b.total_amount || b.Total_Amount;
        const status = b.booking_status || b.Booking_Status;

        const badgeClass = `badge-${status.toLowerCase().replace('_', '')}`;

        html += `
            <tr>
                <td><strong>#${bid}</strong></td>
                <td>${name}</td>
                <td>Room ${roomNum}</td>
                <td>${checkIn} → ${checkOut}</td>
                <td><strong>${fmt(total)}</strong></td>
                <td><span class="badge ${badgeClass}">${status}</span></td>
                <td>
                    <a href="/invoice/${bid}" class="btn btn-outline btn-sm" target="_blank">Folio</a>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

// -----------------------------------------------------------------------------
// BOOKINGS MANAGEMENT
// -----------------------------------------------------------------------------
async function loadAdminBookings(status = '') {
    const tbody = document.getElementById('admin-bookings-tbody');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:32px;">Loading bookings...</td></tr>`;

    try {
        let url = '/api/admin/bookings';
        if (status) url += `?status=${status}`;
        const resp = await apiRequest(url);
        const bookings = resp.bookings;

        if (bookings.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:32px;">No reservations match this filter.</td></tr>`;
            return;
        }

        let html = '';
        bookings.forEach(b => {
            const bid = b.booking_id || b.Booking_ID;
            const name = b.customer_name || b.Customer_Name;
            const phone = b.customer_phone || b.Customer_Phone;
            const roomNum = b.room_number || b.Room_Number;
            const roomType = b.room_type || b.Room_Type;
            const checkIn = b.check_in_date || b.Check_In_Date;
            const checkOut = b.check_out_date || b.Check_Out_Date;
            const total = b.total_amount || b.Total_Amount;
            const status = b.booking_status || b.Booking_Status;
            const badgeClass = `badge-${status.toLowerCase().replace('_', '')}`;

            html += `
                <tr>
                    <td><strong>#${bid}</strong></td>
                    <td>
                        <div><strong>${name}</strong></div>
                        <div style="font-size:0.8rem; color:var(--color-text-muted);">${phone}</div>
                    </td>
                    <td>Room ${roomNum} <br/><span style="font-size:0.75rem; color:var(--color-text-muted);">${roomType}</span></td>
                    <td>${checkIn} to ${checkOut}</td>
                    <td><strong>${fmt(total)}</strong></td>
                    <td><span class="badge ${badgeClass}">${status}</span></td>
                    <td>
                        <select class="input-control" style="padding:4px 8px; font-size:0.8rem;" onchange="updateBookingLifecycle(${bid}, this.value)">
                            <option value="">Update Status...</option>
                            <option value="CHECKED_IN" ${status === 'CHECKED_IN' ? 'disabled' : ''}>Check-In (Occupy Room)</option>
                            <option value="CHECKED_OUT" ${status === 'CHECKED_OUT' ? 'disabled' : ''}>Check-Out (Free Room)</option>
                            <option value="CANCELLED" ${status === 'CANCELLED' ? 'disabled' : ''}>Cancel Reservation</option>
                        </select>
                    </td>
                    <td>
                        <a href="/invoice/${bid}" class="btn btn-dark btn-sm" target="_blank">Invoice</a>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function updateBookingLifecycle(bookingId, newStatus) {
    if (!newStatus) return;
    try {
        const resp = await apiRequest(`/api/admin/bookings/${bookingId}/status`, {
            method: 'PUT',
            body: { status: newStatus }
        });
        showToast(resp.message, 'success');
        loadAdminBookings();
    } catch (err) {
        showToast(`Status update failed: ${err.message}`, 'error');
    }
}

// -----------------------------------------------------------------------------
// ROOMS & ROOM TYPES MANAGEMENT
// -----------------------------------------------------------------------------
async function loadAdminRooms() {
    const tbody = document.getElementById('admin-rooms-tbody');
    if (!tbody) return;

    try {
        const resp = await apiRequest('/api/rooms');
        const rooms = resp.rooms;

        let html = '';
        rooms.forEach(r => {
            const rid = r.room_id || r.Room_ID;
            const rnum = r.room_number || r.Room_Number;
            const floor = r.floor || r.Floor;
            const price = r.price_per_night || r.Price_Per_Night;
            const type = r.type_name || r.Type_Name;
            const status = r.status || r.Status;
            const badgeClass = `badge-${status.toLowerCase()}`;

            html += `
                <tr>
                    <td><strong>${rnum}</strong></td>
                    <td>Floor ${floor}</td>
                    <td>${type}</td>
                    <td><strong>${fmt(price)}</strong></td>
                    <td><span class="badge ${badgeClass}">${status}</span></td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="openEditRoomModal(${rid}, '${rnum}', ${floor}, ${price}, '${status}')">Edit</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteRoom(${rid})">Delete</button>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function deleteRoom(roomId) {
    if (!confirm(`Are you sure you want to delete Room #${roomId}?`)) return;
    try {
        const resp = await apiRequest(`/api/admin/rooms/${roomId}`, { method: 'DELETE' });
        showToast(resp.message, 'success');
        loadAdminRooms();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// -----------------------------------------------------------------------------
// ANALYTICAL REPORTS
// -----------------------------------------------------------------------------
async function loadReport(reportType) {
    const container = document.getElementById('report-results-container');
    if (!container) return;

    container.innerHTML = `<div style="text-align:center; padding:48px;">Executing Oracle Aggregation / View Query...</div>`;

    try {
        const resp = await apiRequest(`/api/admin/reports/${reportType}`);
        const data = resp.data;

        if (reportType === 'monthly-revenue') {
            renderMonthlyRevenueReport(data, container);
        } else if (reportType === 'popular-rooms') {
            renderPopularRoomsReport(data, container);
        } else if (reportType === 'service-usage') {
            renderServiceUsageReport(data, container);
        } else if (reportType === 'top-customers') {
            renderTopCustomersReport(data, container);
        } else if (reportType === 'occupancy-rates') {
            renderOccupancyReport(data, container);
        }
    } catch (err) {
        container.innerHTML = `<div style="color:var(--color-danger); padding:24px;">Report Generation Failed: ${err.message}</div>`;
    }
}

function renderMonthlyRevenueReport(data, container) {
    let html = `
        <div class="table-card">
            <div class="table-header">
                <h3>Monthly Revenue & Collections Report</h3>
                <span class="badge badge-available">Live Oracle View: VW_MONTHLY_REVENUE_REPORT</span>
            </div>
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>Month</th>
                        <th>Total Bookings</th>
                        <th>Gross Booking Value</th>
                        <th>Collected Payments</th>
                    </tr>
                </thead>
                <tbody>
    `;
    data.forEach(row => {
        html += `
            <tr>
                <td><strong>${row.booking_month || row.Booking_Month}</strong></td>
                <td>${row.total_bookings || row.Total_Bookings} stays</td>
                <td><strong>${fmt(row.gross_revenue || row.Gross_Revenue)}</strong></td>
                <td style="color:var(--color-success); font-weight:700;">${fmt(row.collected_amount || row.Collected_Amount)}</td>
            </tr>
        `;
    });
    html += `</tbody></table></div>`;
    container.innerHTML = html;
}

function renderPopularRoomsReport(data, container) {
    let html = `
        <div class="table-card">
            <div class="table-header">
                <h3>Most-Booked Room Categories</h3>
                <span class="badge badge-available">Aggregated GROUP BY & HAVING</span>
            </div>
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>Room Category</th>
                        <th>Base Price</th>
                        <th>Total Bookings</th>
                        <th>Cumulative Revenue</th>
                    </tr>
                </thead>
                <tbody>
    `;
    data.forEach(row => {
        html += `
            <tr>
                <td><strong>${row.type_name || row.Type_Name}</strong></td>
                <td>${fmt(row.base_price || row.Base_Price)} / night</td>
                <td>${row.total_bookings || row.Total_Bookings} bookings</td>
                <td style="font-weight:700; color:var(--color-accent-hover);">${fmt(row.total_revenue || row.Total_Revenue)}</td>
            </tr>
        `;
    });
    html += `</tbody></table></div>`;
    container.innerHTML = html;
}

function renderServiceUsageReport(data, container) {
    let html = `
        <div class="table-card">
            <div class="table-header">
                <h3>Ancillary Hospitality Service Utilization</h3>
                <span class="badge badge-available">Junction Table: BOOKING_SERVICE</span>
            </div>
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>Service Name</th>
                        <th>Category</th>
                        <th>Unit Price</th>
                        <th>Times Ordered</th>
                        <th>Units Sold</th>
                        <th>Revenue Generated</th>
                    </tr>
                </thead>
                <tbody>
    `;
    data.forEach(row => {
        html += `
            <tr>
                <td><strong>${row.service_name || row.Service_Name}</strong></td>
                <td><span class="amenity-pill">${row.category || row.Category}</span></td>
                <td>${fmt(row.unit_price || row.Unit_Price)}</td>
                <td>${row.times_ordered || row.Times_Ordered} times</td>
                <td>${row.total_units || row.Total_Units} units</td>
                <td style="font-weight:700; color:var(--color-success);">${fmt(row.revenue_generated || row.Revenue_Generated)}</td>
            </tr>
        `;
    });
    html += `</tbody></table></div>`;
    container.innerHTML = html;
}

function renderTopCustomersReport(data, container) {
    let html = `
        <div class="table-card">
            <div class="table-header">
                <h3>VIP Customer Leaderboard</h3>
                <span class="badge badge-available">Correlated Aggregates</span>
            </div>
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>Customer Name</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Total Stays</th>
                        <th>Total Spend</th>
                    </tr>
                </thead>
                <tbody>
    `;
    data.forEach(row => {
        html += `
            <tr>
                <td><strong>${row.name || row.Name}</strong></td>
                <td>${row.email || row.Email}</td>
                <td>${row.phone || row.Phone}</td>
                <td>${row.total_stays || row.Total_Stays} reservations</td>
                <td style="font-weight:800; color:var(--color-accent-hover);">${fmt(row.total_spent || row.Total_Spent)}</td>
            </tr>
        `;
    });
    html += `</tbody></table></div>`;
    container.innerHTML = html;
}

function renderOccupancyReport(data, container) {
    let html = `
        <div class="table-card">
            <div class="table-header">
                <h3>Room Inventory Occupancy Summary</h3>
                <span class="badge badge-available">Live Oracle View: VW_ROOM_OCCUPANCY_SUMMARY</span>
            </div>
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Total Rooms</th>
                        <th>Available</th>
                        <th>Occupied</th>
                        <th>Under Maintenance</th>
                    </tr>
                </thead>
                <tbody>
    `;
    data.forEach(row => {
        html += `
            <tr>
                <td><strong>${row.type_name || row.Type_Name}</strong></td>
                <td>${row.total_rooms || row.Total_Rooms}</td>
                <td><span class="badge badge-available">${row.available || row.Available} Available</span></td>
                <td><span class="badge badge-occupied">${row.occupied || row.Occupied} Occupied</span></td>
                <td><span class="badge badge-maintenance">${row.maintenance || row.Maintenance} Maintenance</span></td>
            </tr>
        `;
    });
    html += `</tbody></table></div>`;
    container.innerHTML = html;
}
