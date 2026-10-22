/**
 * Booking Flow & Room Availability Handler
 */

let currentBookingState = {
    roomId: null,
    roomNumber: null,
    roomTypeName: null,
    pricePerNight: 0,
    checkIn: null,
    checkOut: null,
    nights: 1,
    guests: 1,
    selectedServices: []
};

// Initialize Date Defaults on Page Load
document.addEventListener('DOMContentLoaded', () => {
    const checkInInput = document.getElementById('search-checkin');
    const checkOutInput = document.getElementById('search-checkout');

    if (checkInInput && checkOutInput) {
        const today = new Date();
        const checkInDate = new Date(today);
        checkInDate.setDate(today.getDate() + 1);
        const checkOutDate = new Date(today);
        checkOutDate.setDate(today.getDate() + 4);

        const formatDate = (d) => d.toISOString().split('T')[0];

        checkInInput.min = formatDate(today);
        checkInInput.value = formatDate(checkInDate);
        
        checkOutInput.min = formatDate(checkInDate);
        checkOutInput.value = formatDate(checkOutDate);

        checkInInput.addEventListener('change', () => {
            const nextDay = new Date(checkInInput.value);
            nextDay.setDate(nextDay.getDate() + 1);
            checkOutInput.min = formatDate(nextDay);
            if (checkOutInput.value <= checkInInput.value) {
                checkOutInput.value = formatDate(nextDay);
            }
        });
    }

    // Bind Search Form
    const searchForm = document.getElementById('booking-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            executeRoomSearch();
        });
    }

    // Auto-search if on rooms page with query params
    if (window.location.pathname === '/rooms') {
        const params = new URLSearchParams(window.location.search);
        if (params.get('check_in') && params.get('check_out')) {
            if (checkInInput) checkInInput.value = params.get('check_in');
            if (checkOutInput) checkOutInput.value = params.get('check_out');
            executeRoomSearch();
        }
    }
});

async function executeRoomSearch() {
    const checkIn = document.getElementById('search-checkin')?.value;
    const checkOut = document.getElementById('search-checkout')?.value;
    const guests = document.getElementById('search-guests')?.value || 1;
    const roomTypeId = document.getElementById('search-roomtype')?.value || '';

    if (!checkIn || !checkOut) {
        showToast('Please select valid check-in and check-out dates.', 'error');
        return;
    }

    const resultsContainer = document.getElementById('search-results-container');
    if (!resultsContainer) return;

    resultsContainer.innerHTML = `
        <div style="text-align:center; padding: 48px; color: var(--color-text-muted);">
            <div style="font-size:2rem; margin-bottom:12px;">⏳</div>
            <p>Verifying live inventory and checking date range overlaps...</p>
        </div>
    `;

    try {
        let url = `/api/rooms/available?check_in=${checkIn}&check_out=${checkOut}&guests=${guests}`;
        if (roomTypeId) url += `&room_type_id=${roomTypeId}`;

        const resp = await apiRequest(url);
        const data = resp.data;

        currentBookingState.checkIn = data.check_in;
        currentBookingState.checkOut = data.check_out;
        currentBookingState.nights = data.nights;
        currentBookingState.guests = data.guests;

        renderAvailableRooms(data.rooms, resultsContainer);
    } catch (err) {
        resultsContainer.innerHTML = `
            <div style="text-align:center; padding: 48px; color: var(--color-danger);">
                <div style="font-size:2rem; margin-bottom:12px;">⚠️</div>
                <p><strong>Availability Check Failed:</strong> ${err.message}</p>
            </div>
        `;
        showToast(err.message, 'error');
    }
}

function renderAvailableRooms(rooms, container) {
    if (!rooms || rooms.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding: 48px; background: white; border-radius: var(--radius-lg); border: 1px dashed var(--color-border);">
                <div style="font-size:2.5rem; margin-bottom:12px;">🏨</div>
                <h3 style="margin-bottom:8px;">No Rooms Available For These Dates</h3>
                <p style="color:var(--color-text-muted); max-width:480px; margin:0 auto 16px;">All rooms in this tier have conflicting active reservations for the selected date range. Please select alternative dates or room styles.</p>
            </div>
        `;
        return;
    }

    let html = `<div class="rooms-grid">`;
    rooms.forEach(room => {
        const rId = room.room_id || room.Room_ID;
        const rNum = room.room_number || room.Room_Number;
        const floor = room.floor || room.Floor;
        const price = room.price_per_night || room.Price_Per_Night;
        const typeName = room.type_name || room.Type_Name;
        const desc = room.description || room.Description;
        const maxOcc = room.max_occupancy || room.Max_Occupancy;
        const img = room.image_url || room.Image_URL || 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80';
        const amenities = (room.amenities || room.Amenities || '').split(',').map(a => `<span class="amenity-pill">${a.trim()}</span>`).join('');
        const totalEst = room.total_estimated_cost || room.Total_Estimated_Cost || (price * currentBookingState.nights);

        html += `
            <div class="room-card">
                <div class="room-card-img-wrapper">
                    <img src="${img}" alt="${typeName}" class="room-card-img" />
                    <div class="room-price-badge">
                        $${price} <span>/ night</span>
                    </div>
                </div>
                <div class="room-card-body">
                    <div class="room-type-tag">${typeName} • Floor ${floor} • Room ${rNum}</div>
                    <h3 class="room-card-title">${typeName}</h3>
                    <p class="room-card-desc">${desc}</p>
                    <div class="room-amenity-tags">${amenities}</div>
                    <div class="room-card-footer">
                        <div class="occupancy-info">
                            <span>👥 Up to ${maxOcc} guests</span> • <span>${currentBookingState.nights} night(s): <strong>$${totalEst}</strong></span>
                        </div>
                        <button class="btn btn-primary btn-sm" onclick="initiateBookingModal(${rId}, '${rNum}', '${typeName}', ${price})">
                            Book Room
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    html += `</div>`;
    container.innerHTML = html;
}

// Open Checkout Modal
async function initiateBookingModal(roomId, roomNumber, roomTypeName, pricePerNight) {
    currentBookingState.roomId = roomId;
    currentBookingState.roomNumber = roomNumber;
    currentBookingState.roomTypeName = roomTypeName;
    currentBookingState.pricePerNight = pricePerNight;
    currentBookingState.selectedServices = [];

    // Check if user is logged in
    try {
        const authResp = await apiRequest('/api/auth/me');
        if (!authResp.authenticated) {
            showToast('Please log in to complete your reservation.', 'info');
            setTimeout(() => {
                window.location.href = `/login?next=${encodeURIComponent(window.location.href)}`;
            }, 1000);
            return;
        }
    } catch (e) {}

    // Populate modal fields
    document.getElementById('modal-room-type').textContent = roomTypeName;
    document.getElementById('modal-room-meta').textContent = `Room #${roomNumber} • $${pricePerNight} per night`;
    document.getElementById('modal-checkin-val').textContent = currentBookingState.checkIn;
    document.getElementById('modal-checkout-val').textContent = currentBookingState.checkOut;
    document.getElementById('modal-nights-val').textContent = `${currentBookingState.nights} night(s)`;

    // Load available services
    loadModalServices();
    recalculateModalPricing();
    openModal('booking-modal');
}

async function loadModalServices() {
    const srvContainer = document.getElementById('modal-services-list');
    if (!srvContainer) return;

    try {
        const resp = await apiRequest('/api/services');
        const services = resp.services;
        let html = '';
        services.forEach(s => {
            const sid = s.service_id || s.Service_ID;
            const name = s.service_name || s.Service_Name;
            const price = s.price || s.Price;
            html += `
                <label style="display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#f8fafc; border-radius:var(--radius-sm); border:1px solid var(--color-border); cursor:pointer;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <input type="checkbox" value="${sid}" data-price="${price}" onchange="toggleService(${sid}, ${price}, this.checked)" />
                        <span style="font-size:0.9rem; font-weight:500;">${name}</span>
                    </div>
                    <span style="font-weight:700; color:var(--color-accent-hover); font-size:0.9rem;">+$${price}</span>
                </label>
            `;
        });
        srvContainer.innerHTML = html;
    } catch (e) {
        srvContainer.innerHTML = '<p style="color:var(--color-text-muted); font-size:0.85rem;">Could not load add-on services.</p>';
    }
}

function toggleService(serviceId, price, isChecked) {
    if (isChecked) {
        currentBookingState.selectedServices.push({ service_id: serviceId, price: price, quantity: 1 });
    } else {
        currentBookingState.selectedServices = currentBookingState.selectedServices.filter(s => s.service_id !== serviceId);
    }
    recalculateModalPricing();
}

function recalculateModalPricing() {
    const roomCharge = currentBookingState.pricePerNight * currentBookingState.nights;
    let serviceCharge = 0;
    currentBookingState.selectedServices.forEach(s => serviceCharge += (s.price * s.quantity));
    
    const subtotal = roomCharge + serviceCharge;
    const tax = Math.round(subtotal * 0.12 * 100) / 100;
    const grandTotal = Math.round((subtotal + tax) * 100) / 100;

    document.getElementById('modal-room-charge').textContent = `$${roomCharge.toFixed(2)}`;
    document.getElementById('modal-service-charge').textContent = `$${serviceCharge.toFixed(2)}`;
    document.getElementById('modal-tax-charge').textContent = `$${tax.toFixed(2)}`;
    document.getElementById('modal-grand-total').textContent = `$${grandTotal.toFixed(2)}`;
}

async function confirmBookingSubmission() {
    const submitBtn = document.getElementById('modal-confirm-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Executing PL/SQL Procedure...';

    const payload = {
        room_id: currentBookingState.roomId,
        check_in: currentBookingState.checkIn,
        check_out: currentBookingState.checkOut,
        no_of_guests: currentBookingState.guests,
        payment_mode: document.getElementById('modal-payment-mode')?.value || 'CREDIT_CARD',
        services: currentBookingState.selectedServices
    };

    try {
        const resp = await apiRequest('/api/bookings', {
            method: 'POST',
            body: payload
        });

        showToast(resp.message, 'success');
        closeModal('booking-modal');
        setTimeout(() => {
            window.location.href = resp.invoice_url;
        }, 1200);
    } catch (err) {
        showToast(`Booking Failed: ${err.message}`, 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Confirm & Pay';
    }
}
