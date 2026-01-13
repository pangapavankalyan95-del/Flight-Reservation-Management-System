// ==================== SEARCH & FILTERS ====================

let currentBooking = {};

document.addEventListener('DOMContentLoaded', function () {
    // Set minimum date to today
    if (document.getElementById('date')) {
        document.getElementById('date').min = new Date().toISOString().split('T')[0];
    }

    // Search form submission
    if (document.getElementById('searchForm')) {
        document.getElementById('searchForm').addEventListener('submit', function (e) {
            e.preventDefault();
            searchFlights();
        });
    }

    // Filter event listeners
    ['minPrice', 'maxPrice', 'timeFilter', 'sortFilter'].forEach(id => {
        if (document.getElementById(id)) {
            document.getElementById(id).addEventListener('change', applyFilters);
        }
    });

    // Debounce price input
    ['minPrice', 'maxPrice'].forEach(id => {
        if (document.getElementById(id)) {
            document.getElementById(id).addEventListener('input', debounce(applyFilters, 500));
        }
    });
});

async function searchFlights() {
    const source = document.getElementById('source').value;
    const destination = document.getElementById('destination').value;
    const date = document.getElementById('date').value;

    if (!source || !destination || !date) {
        alert('Please fill in all fields');
        return;
    }

    // Show loading
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('noResults').style.display = 'none';
    document.getElementById('filtersSection').style.display = 'none';

    try {
        const response = await fetch(`/api/flights/search?source=${encodeURIComponent(source)}&destination=${encodeURIComponent(destination)}&date=${date}`);
        const data = await response.json();

        document.getElementById('loadingSpinner').style.display = 'none';

        if (response.ok && data.flights.length > 0) {
            // Store flights globally for filtering
            window.allFlights = data.flights;
            displayFlights(data.flights);
            // Show filters section
            const filtersSection = document.getElementById('filtersSection');
            if (filtersSection) {
                filtersSection.style.display = 'block';
            }
        } else {
            document.getElementById('noResults').style.display = 'block';
            if (document.getElementById('filtersSection')) document.getElementById('filtersSection').style.display = 'none';
            // Auto-scroll to no results message
            setTimeout(() => {
                document.getElementById('noResults').scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }, 100);
        }
    } catch (error) {
        console.error('Error searching flights:', error);
        document.getElementById('loadingSpinner').style.display = 'none';
        alert('An error occurred while searching for flights');
    }
}

function displayFlights(flights) {
    const resultsContainer = document.getElementById('flightResults');

    resultsContainer.innerHTML = flights.map(flight => `
        <div class="col-md-6 col-lg-4 fade-in">
            <div class="flight-card">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div class="flight-number">
                        <i class="bi bi-airplane-fill me-2"></i>${flight.flight_number}
                    </div>
                    <div class="text-end">
                        <div class="fw-bold text-primary">${flight.airline || 'Airline'}</div>
                        <small class="text-muted" style="font-size: 0.75rem;">${flight.aircraft || 'Aircraft'}</small>
                    </div>
                </div>
                
                <div class="flight-route">
                    <div class="flight-location">
                        <h5>${flight.source}</h5>
                        <small>${formatTime(flight.departure_time)}</small>
                    </div>
                    <div class="flight-arrow">
                        <i class="bi bi-arrow-right"></i>
                    </div>
                    <div class="flight-location">
                        <h5>${flight.destination}</h5>
                        <small>${formatTime(flight.arrival_time)}</small>
                    </div>
                </div>
                
                <div class="flight-details">
                    <div class="flight-info">
                        <i class="bi bi-calendar-fill"></i>
                        <strong>${formatDate(flight.date)}</strong>
                        <small>Date</small>
                    </div>
                    <div class="flight-info">
                        <i class="bi bi-currency-rupee"></i>
                        <strong>${flight.price.toFixed(2)}</strong>
                        <small>Price</small>
                    </div>
                    <div class="flight-info">
                        <i class="bi bi-people-fill"></i>
                        <strong>${flight.available_seats}</strong>
                        <small>Seats</small>
                    </div>
                </div>
                
                <button class="btn btn-primary w-100 mt-3" onclick="openBookingModal(${flight.flight_id}, '${flight.flight_number}', '${flight.source}', '${flight.destination}', '${flight.date}', ${flight.price}, ${flight.available_seats})">
                    <i class="bi bi-ticket-fill me-2"></i>Book Now
                </button>
            </div>
        </div>
    `).join('');

    document.getElementById('resultsSection').style.display = 'block';

    // Update flight count badge
    if (document.getElementById('flightCount')) {
        document.getElementById('flightCount').textContent = flights.length;
    }

    // Auto-scroll to results section smoothly
    setTimeout(() => {
        document.getElementById('resultsSection').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }, 100);
}

function applyFilters() {
    if (!window.allFlights) return;

    let filteredFlights = [...window.allFlights];

    // Price filter
    const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
    const maxPrice = parseFloat(document.getElementById('maxPrice').value) || 999999;
    filteredFlights = filteredFlights.filter(f => f.price >= minPrice && f.price <= maxPrice);

    // Time filter
    const timeFilter = document.getElementById('timeFilter').value;
    if (timeFilter !== 'all') {
        filteredFlights = filteredFlights.filter(f => {
            const hour = parseInt(f.departure_time.split(':')[0]);
            if (timeFilter === 'morning') return hour >= 6 && hour < 12;
            if (timeFilter === 'afternoon') return hour >= 12 && hour < 18;
            if (timeFilter === 'evening') return hour >= 18 || hour < 6;
            return true;
        });
    }

    // Sorting
    const sortFilter = document.getElementById('sortFilter').value;
    if (sortFilter === 'price-asc') {
        filteredFlights.sort((a, b) => a.price - b.price);
    } else if (sortFilter === 'price-desc') {
        filteredFlights.sort((a, b) => b.price - a.price);
    } else if (sortFilter === 'time-asc') {
        filteredFlights.sort((a, b) => a.departure_time.localeCompare(b.departure_time));
    } else if (sortFilter === 'time-desc') {
        filteredFlights.sort((a, b) => b.departure_time.localeCompare(a.departure_time));
    }

    if (filteredFlights.length > 0) {
        displayFlights(filteredFlights);
    } else {
        document.getElementById('resultsSection').style.display = 'block';
        document.getElementById('flightResults').innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="bi bi-filter-circle text-muted" style="font-size: 3rem;"></i>
                <h4 class="mt-3 text-muted">No flights match your filters</h4>
                <button class="btn btn-outline-primary mt-2" onclick="resetFilters()">Reset Filters</button>
            </div>
        `;
        document.getElementById('flightCount').textContent = '0';
    }
}

function resetFilters() {
    document.getElementById('minPrice').value = 0;
    document.getElementById('maxPrice').value = 20000;
    document.getElementById('timeFilter').value = 'all';
    document.getElementById('sortFilter').value = 'price-asc';
    displayFlights(window.allFlights);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(timeStr) {
    if (!timeStr) return '';
    const [hours, minutes] = timeStr.split(':');
    let hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    hour = hour % 12;
    hour = hour ? hour : 12;
    return `${hour}:${minutes} ${ampm}`;
}

// ==================== BOOKING WIZARD ====================

function openBookingModal(flightId, flightNumber, source, destination, date, price, availableSeats) {
    // Check if user is logged in
    fetch('/api/check-auth')
        .then(response => response.json())
        .then(data => {
            if (!data.authenticated) {
                alert('Please login to book flights');
                window.location.href = '/login';
                return;
            }

            // Init State
            currentBooking = {
                flightId, flightNumber, source, destination, date, basePrice: price,
                class: null,
                seats: [], // Array for multiple seats
                seatsBooked: 0,
                multiplier: 1,
                isGroup: false
            };

            // Setup
            renderClassOptions();
            switchStep('class');

            const modal = new bootstrap.Modal(document.getElementById('bookingModal'));
            modal.show();
        });
}

function isInternationalFlight(source, dest) {
    const international = ['Dubai', 'London', 'New York', 'Singapore', 'Bangkok'];
    // Simple check: if either endpoint is international
    // Note: Data might have "(DXB)" etc. so we use check string inclusion
    const isIntl = (city) => international.some(i => city.includes(i));
    return isIntl(source) || isIntl(dest);
}

function renderClassOptions() {
    const container = document.getElementById('classOptions');
    const isIntl = isInternationalFlight(currentBooking.source, currentBooking.destination);
    const suffix = isIntl ? 'int' : 'dom';

    // Define classes
    const classes = [
        { id: 'Economy', name: 'Economy Class', mult: 1, img: `cabin_eco_${suffix}.png`, desc: 'Comfortable seating with great service.' },
        { id: 'Business', name: 'Business Class', mult: 2.5, img: `cabin_bus_${suffix}.png`, desc: 'Premium seating, extra legroom, and priority.' },
        { id: 'First', name: 'First Class', mult: 4, img: `cabin_first_${suffix}.png`, desc: 'Absolute luxury, privacy, and fine dining.' }
    ];

    container.innerHTML = classes.map(c => `
        <div class="col-md-4">
            <div class="class-card h-100" onclick="selectClass('${c.id}', ${c.mult})" id="card-${c.id}">
                <img src="/static/img/${c.img}" class="class-img" alt="${c.name}">
                <div class="p-3">
                    <h6 class="fw-bold mb-1">${c.name}</h6>
                    <small class="text-muted d-block mb-2" style="font-size:0.75rem">${c.desc}</small>
                    <div class="text-primary fw-bold">₹${(currentBooking.basePrice * c.mult).toFixed(0)}</div>
                </div>
            </div>
        </div>
    `).join('');
}

function selectClass(className, multiplier) {
    currentBooking.class = className;
    currentBooking.multiplier = multiplier;

    // Highlight UI
    document.querySelectorAll('.class-card').forEach(el => el.classList.remove('selected'));
    document.getElementById(`card-${className}`).classList.add('selected');

    // Move to next step with slight delay
    setTimeout(() => {
        switchStep('seat');
    }, 300);
}

function toggleGroupBooking() {
    const isChecked = document.getElementById('groupBookingToggle').checked;
    currentBooking.isGroup = isChecked;

    // Reset seats if we toggle off and have too many or just to be safe/clean
    if (!isChecked && currentBooking.seats.length > 5) {
        // Clear all to avoid confusion or just keep first 5? 
        // Let's clear for simplicity or notify user. For now, clear.
        currentBooking.seats = [];
        document.querySelectorAll('.seat.selected').forEach(s => s.classList.remove('selected'));
        updateSeatUI();
    }
}

function renderSeatMap() {
    console.log("Rendering Seat Map...");
    const grid = document.getElementById('seatGrid');
    if (!grid) {
        console.error("Seat Grid Element Not Found!");
        return;
    }

    grid.innerHTML = ''; // Clear existing

    for (let r = 1; r <= 8; r++) { // 8 Rows
        const row = document.createElement('div');
        row.className = 'seat-row';
        // Force flex display in style to be sure
        row.style.display = 'flex';
        row.style.gap = '10px';
        row.style.justifyContent = 'center';
        row.style.marginBottom = '10px';

        ['A', 'B', 'C', '', 'D', 'E', 'F'].forEach(col => {
            if (col === '') {
                const aisle = document.createElement('div');
                aisle.className = 'seat-aisle';
                aisle.innerText = r;
                aisle.style.width = '30px';
                aisle.style.textAlign = 'center';
                aisle.style.lineHeight = '40px'; // Vertically center
                row.appendChild(aisle);
            } else {
                const seatId = `${r}${col}`;
                const seat = document.createElement('div');
                seat.className = 'seat';
                seat.innerText = col;

                // Inline styles to guarantee visibility even if CSS fails
                seat.style.width = '40px';
                seat.style.height = '40px';
                seat.style.display = 'flex';
                seat.style.alignItems = 'center';
                seat.style.justifyContent = 'center';
                seat.style.border = '1px solid #ccc';
                seat.style.borderRadius = '8px';
                seat.style.cursor = 'pointer';
                // Re-apply selection state
                if (currentBooking.seats.includes(seatId)) {
                    seat.classList.add('selected');
                }

                seat.onclick = () => selectSeat(seatId, seat);

                // Deterministic occupancy
                let hash = 0;
                for (let i = 0; i < seatId.length; i++) hash += seatId.charCodeAt(i);

                if ((hash % 10) < 2 && !currentBooking.seats.includes(seatId)) {
                    seat.classList.add('occupied');
                    seat.style.cursor = 'not-allowed';
                    seat.onclick = null;
                }

                row.appendChild(seat);
            }
        });
        console.log(`Appended Row ${r}`);
        grid.appendChild(row);
    }
    console.log("Seat Map Rendered.");
}

function selectSeat(seatId, el) {
    if (el.classList.contains('occupied')) return;

    const limit = currentBooking.isGroup ? 10 : 5;

    // Check if already selected
    const index = currentBooking.seats.indexOf(seatId);
    if (index > -1) {
        // Deselect
        currentBooking.seats.splice(index, 1);
        el.classList.remove('selected');
    } else {
        // Select
        if (currentBooking.seats.length >= limit) {
            alert(`You can only select up to ${limit} seats.${currentBooking.isGroup ? '' : ' Enable Group Booking for up to 10.'}`);
            return;
        }
        currentBooking.seats.push(seatId);
        el.classList.add('selected');
    }

    updateSeatUI();
}

function updateSeatUI() {
    const count = currentBooking.seats.length;
    currentBooking.seatsBooked = count; // Update count

    // Update display text
    const txt = count > 0 ? currentBooking.seats.join(', ') : '-';
    document.getElementById('selectedSeatsDisplay').innerText = txt;

    // Enable button if at least 1 seat
    document.getElementById('btnConfirmSeat').disabled = (count === 0);
}

function renderSummary() {
    document.getElementById('finalFlightInfo').innerText = currentBooking.flightNumber;
    document.getElementById('finalClass').innerText = currentBooking.class;
    document.getElementById('finalSeat').innerText = currentBooking.seats.join(', ');

    const total = currentBooking.basePrice * currentBooking.multiplier * currentBooking.seatsBooked;
    document.getElementById('finalPrice').innerText = `₹${total.toFixed(0)}`;
}

function switchStep(stepId) {
    // Hide all
    document.querySelectorAll('.wizard-step').forEach(el => el.style.display = 'none');

    // Show target
    document.getElementById(`step-${stepId}`).style.display = 'block';

    // Init logic
    if (stepId === 'seat') {
        const classDisplay = document.getElementById('selectedClassDisplay');
        if (classDisplay) {
            classDisplay.innerText = currentBooking.class;
            classDisplay.className = `badge bg-${currentBooking.class === 'First' ? 'warning text-dark' : (currentBooking.class === 'Business' ? 'info text-dark' : 'secondary')}`;
        }

        // Always render to ensure visibility and re-apply selection state
        renderSeatMap();

    } else if (stepId === 'passenger') {
        renderPassengerInputs();
        renderSummary();
    }
}

function renderPassengerInputs() {
    const container = document.getElementById('passengerInputsContainer');
    container.innerHTML = '';

    currentBooking.seats.forEach((seat, index) => {
        container.innerHTML += `
            <div class="mb-3">
                <label class="form-label">Passenger ${index + 1} (Seat ${seat})</label>
                <input type="text" class="form-control passenger-name-input" data-index="${index}" placeholder="Full Name of Passenger ${index + 1}" required>
            </div>
        `;
    });
}

async function processBooking() {
    // Gather names
    const inputs = document.querySelectorAll('.passenger-name-input');
    const names = [];
    let missing = false;

    inputs.forEach(input => {
        const val = input.value.trim();
        if (!val) missing = true;
        names.push(val); // e.g., ["John", "Jane"]
    });

    if (missing) {
        alert('Please enter all passenger names');
        return;
    }

    // Format: "John Doe (1A), Jane Doe (1B)" or just comma separated?
    // User asked: "no.of seats booked if 2 ticckets ae booked tehn 2 persons should be displayes"
    // We will join names with comma.
    const passengerString = names.join(', ');
    const seatString = currentBooking.seats.join(', ');

    // Show loading
    switchStep('success');

    // Simulate payment delay
    setTimeout(async () => {
        try {
            const response = await fetch('/api/bookings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    flight_id: parseInt(currentBooking.flightId),
                    seats_booked: currentBooking.seatsBooked,
                    passenger_names: passengerString,
                    booking_class: currentBooking.class,
                    seat_numbers: seatString
                })
            });
            const data = await response.json();

            if (response.ok) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('bookingModal'));
                modal.hide();
                alert(`Payment Successful! Tickets Confirmed.\nBooking ID: #${data.booking_id}`);
                window.location.href = '/bookings';
            } else {
                alert(data.error || 'Booking failed');
                switchStep('passenger');
            }
        } catch (e) {
            console.error(e);
            alert('Error processing booking');
            switchStep('passenger');
        }
    }, 2000); // 2s payment simulation
}

// ==================== UTILITY FUNCTIONS ====================

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    // Auto hide after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}

// ==================== AUTHENTICATION ====================

function checkAuthStatus() {
    fetch('/api/check-auth')
        .then(response => response.json())
        .then(data => {
            if (data.authenticated) {
                // Logged in
                if (document.getElementById('nav-login')) document.getElementById('nav-login').style.display = 'none';
                if (document.getElementById('nav-signup')) document.getElementById('nav-signup').style.display = 'none';

                if (document.getElementById('nav-user')) {
                    document.getElementById('nav-user').style.display = 'block';
                    document.getElementById('user-name-display').textContent = data.user.name;
                }
                if (document.getElementById('nav-bookings')) document.getElementById('nav-bookings').style.display = 'block';

                // Admin check
                if (data.user.is_admin && document.getElementById('nav-admin')) {
                    document.getElementById('nav-admin').style.display = 'block';
                }
            } else {
                // Not logged in
                if (document.getElementById('nav-login')) document.getElementById('nav-login').style.display = 'block';
                if (document.getElementById('nav-signup')) document.getElementById('nav-signup').style.display = 'block';
                if (document.getElementById('nav-user')) document.getElementById('nav-user').style.display = 'none';
                if (document.getElementById('nav-bookings')) document.getElementById('nav-bookings').style.display = 'none';
                if (document.getElementById('nav-admin')) document.getElementById('nav-admin').style.display = 'none';
            }
        })
        .catch(err => console.error('Auth check failed', err));
}

function logout() {
    fetch('/api/logout')
        .then(() => {
            window.location.href = '/login';
        });
}
