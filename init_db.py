import sqlite3
from datetime import datetime, timedelta
import os
import random
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize the database with tables and sample data"""
    
    # Remove existing database if it exists
    if os.path.exists('flight_reservation.db'):
        os.remove('flight_reservation.db')
    
    conn = sqlite3.connect('flight_reservation.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create flights table with new columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number TEXT UNIQUE NOT NULL,
            airline TEXT DEFAULT 'Standard Air',
            aircraft TEXT DEFAULT 'Boeing 737',
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            date TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            arrival_time TEXT NOT NULL,
            price REAL NOT NULL,
            total_seats INTEGER NOT NULL,
            available_seats INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            flight_id INTEGER NOT NULL,
            seats_booked INTEGER NOT NULL,
            booking_class TEXT DEFAULT 'Economy',
            seat_numbers TEXT,
            passenger_names TEXT NOT NULL,
            total_price REAL NOT NULL,
            booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'confirmed',
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
        )
    ''')
    
    # === GENERATE REALISTIC FLIGHT DATA ===
    print("🚀 Generating realistic flight data...")
    
    airlines_data = [
        {"name": "Air India", "code": "AI", "models": ["Boeing 787 Dreamliner", "Boeing 777-300ER", "Airbus A321neo"]},
        {"name": "IndiGo", "code": "6E", "models": ["Airbus A320neo", "Airbus A321neo"]},
        {"name": "Vistara", "code": "UK", "models": ["Boeing 787-9", "Airbus A321neo"]},
        {"name": "SpiceJet", "code": "SG", "models": ["Boeing 737 MAX", "Q400"]},
        {"name": "Emirates", "code": "EK", "models": ["Airbus A380", "Boeing 777-300ER"]},
        {"name": "British Airways", "code": "BA", "models": ["Boeing 787", "Airbus A350-1000"]},
        {"name": "Lufthansa", "code": "LH", "models": ["Boeing 747-8", "Airbus A350"]},
        {"name": "Singapore Airlines", "code": "SQ", "models": ["Airbus A350-900", "Boeing 787-10"]},
        {"name": "Qatar Airways", "code": "QR", "models": ["Airbus A350-1000", "Boeing 777"]}
    ]
    
    airports = {
        "Domestic": [
            "Delhi (DEL)", "Mumbai (BOM)", "Bangalore (BLR)", "Chennai (MAA)", 
            "Kolkata (CCU)", "Hyderabad (HYD)", "Pune (PNQ)", "Goa (GOI)",
            "Ahmedabad (AMD)", "Jaipur (JAI)"
        ],
        "International": [
            "Dubai (DXB)", "London (LHR)", "New York (JFK)", "Singapore (SIN)", 
            "Bangkok (BKK)", "Paris (CDG)", "Frankfurt (FRA)", "Tokyo (HND)"
        ]
    }
    
    today = datetime.now()
    all_flights = []
    flight_set = set() # To prevent duplicate flight numbers per day (though flight_num is unique in DB, we append suffixes)
    
    # Generate for 60 days
    for day_offset in range(60): 
        current_date_obj = today + timedelta(days=day_offset)
        current_date = current_date_obj.strftime('%Y-%m-%d')
        
        # Determine number of flights for this day (20-30 flights)
        num_flights = random.randint(20, 30)
        
        for idx in range(num_flights):
            # 70% chance Domestic, 30% International
            if random.random() < 0.7:
                flight_type = "Domestic"
                source = random.choice(airports["Domestic"])
                dest = random.choice([a for a in airports["Domestic"] if a != source])
                valid_airlines = [a for a in airlines_data if a["name"] in ["Air India", "IndiGo", "Vistara", "SpiceJet"]]
                base_price = 3000
                duration_min = 90
                duration_max = 180
            else:
                flight_type = "International"
                # Either Source or Dest is Indian (mostly)
                if random.random() < 0.5:
                    source = random.choice(airports["Domestic"])
                    dest = random.choice(airports["International"])
                else:
                    source = random.choice(airports["International"])
                    dest = random.choice(airports["Domestic"])
                    
                valid_airlines = airlines_data # All airlines fly international
                base_price = 15000
                duration_min = 240
                duration_max = 900
            
            airline = random.choice(valid_airlines)
            aircraft = random.choice(airline["models"])
            
            # Unique Flight Number: Code + Day + Index + Random
            flight_code = f"{airline['code']}{day_offset}{idx}{random.randint(10, 99)}"
            
            # Time
            hour = random.randint(0, 23)
            minute = random.choice([0, 15, 30, 45])
            dep_time_str = f"{hour:02d}:{minute:02d}"
            
            # Duration calculation
            duration = random.randint(duration_min, duration_max)
            dep_dt = datetime.strptime(f"{current_date} {dep_time_str}", '%Y-%m-%d %H:%M')
            arr_dt = dep_dt + timedelta(minutes=duration)
            
            # If arrival is next day, it's fine, we just store time or full date? 
            # DB has `arrival_time TEXT`. Usually just time.
            arr_time_str = arr_dt.strftime('%H:%M')
            # Note: Arrival might be next day, frontend currently ignores date diff for arrival.
            
            # Price
            price = base_price + (duration * 10) + random.randint(-500, 2000)
            price = round(price, -1) # Round to nearest 10
            
            seats = random.choice([150, 180, 220, 300]) if "Broad" not in aircraft else 400
            avail = int(seats * random.uniform(0.1, 0.9)) # Random availability
            
            all_flights.append((
                flight_code, airline["name"], aircraft, source, dest, current_date, 
                dep_time_str, arr_time_str, price, seats, avail
            ))
            
    cursor.executemany('''
        INSERT INTO flights (flight_number, airline, aircraft, source, destination, date, departure_time, arrival_time, price, total_seats, available_seats)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', all_flights)
    
    # Create a demo admin user (password: admin123)
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT INTO users (name, email, password_hash, is_admin)
        VALUES (?, ?, ?, ?)
    ''', ('Admin User', 'admin@flight.com', admin_password, 1))
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully!")
    print(f"✅ Created {len(all_flights)} sample flights across 60 days")
    print("✅ Created admin user: admin@flight.com / admin123")

if __name__ == '__main__':
    init_database()
