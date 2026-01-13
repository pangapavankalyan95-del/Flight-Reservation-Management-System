import random
from datetime import datetime, timedelta
import sqlite3

AIRLINES_DATA = [
    {"name": "Air India", "code": "AI", "models": ["Boeing 787 Dreamliner", "Boeing 777-300ER", "Airbus A321neo"]},
    {"name": "IndiGo", "code": "6E", "models": ["Airbus A320neo", "Airbus A321neo"]},
    {"name": "Vistara", "code": "UK", "models": ["Boeing 787-9", "Airbus A321neo"]},
    {"name": "SpiceJet", "code": "SG", "models": ["Boeing 737 MAX", "Q400"]},
    {"name": "Akasa Air", "code": "QP", "models": ["Boeing 737 MAX"]},
    {"name": "Emirates", "code": "EK", "models": ["Airbus A380", "Boeing 777-300ER"]},
    {"name": "British Airways", "code": "BA", "models": ["Boeing 787", "Airbus A350-1000"]},
    {"name": "Lufthansa", "code": "LH", "models": ["Boeing 747-8", "Airbus A350"]},
    {"name": "Singapore Airlines", "code": "SQ", "models": ["Airbus A350-900", "Boeing 787-10"]},
    {"name": "Qatar Airways", "code": "QR", "models": ["Airbus A350-1000", "Boeing 777"]}
]

AIRPORTS = {
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

def generate_flights(conn, count=100):
    """Generate 'count' realistic dummy flights"""
    
    today = datetime.now()
    all_flights = []
    
    print(f"✈️ Generating {count} new flights...")
    
    for _ in range(count):
        # Weighted random date (mostly next 30 days)
        days_ahead = random.randint(1, 45)
        current_date_obj = today + timedelta(days=days_ahead)
        date_str = current_date_obj.strftime('%Y-%m-%d')
        
        # 70% Domestic
        if random.random() < 0.7:
            flight_type = "Domestic"
            source = random.choice(AIRPORTS["Domestic"])
            dest = random.choice([a for a in AIRPORTS["Domestic"] if a != source])
            valid_airlines = [a for a in AIRLINES_DATA if a["name"] in ["Air India", "IndiGo", "Vistara", "SpiceJet", "Akasa Air"]]
            base_price = 3000
            duration_min, duration_max = 90, 180
        else:
            flight_type = "International"
            if random.random() < 0.5:
                source = random.choice(AIRPORTS["Domestic"])
                dest = random.choice(AIRPORTS["International"])
            else:
                source = random.choice(AIRPORTS["International"])
                dest = random.choice(AIRPORTS["Domestic"])
            valid_airlines = AIRLINES_DATA
            base_price = 15000
            duration_min, duration_max = 240, 900
            
        airline = random.choice(valid_airlines)
        aircraft = random.choice(airline["models"])
        
        # Generate Code
        flight_code = f"{airline['code']}{random.randint(100, 9999)}"
        
        # Time
        hour = random.randint(0, 23)
        minute = random.choice([0, 5, 10, 15, 30, 45])
        dep_time_str = f"{hour:02d}:{minute:02d}"
        
        # Arrival
        duration = random.randint(duration_min, duration_max)
        dep_dt = datetime.strptime(f"{date_str} {dep_time_str}", '%Y-%m-%d %H:%M')
        arr_dt = dep_dt + timedelta(minutes=duration)
        arr_time_str = arr_dt.strftime('%H:%M')
        
        # Price & Seats
        price = base_price + (duration * 10) + random.randint(-500, 2000)
        price = round(price, -1)
        
        seats = random.choice([150, 180, 220, 300])
        avail = int(seats * random.uniform(0.1, 0.9))
        
        all_flights.append((
            flight_code, airline["name"], aircraft, source, dest, date_str, 
            dep_time_str, arr_time_str, price, seats, avail
        ))
        
    try:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO flights (flight_number, airline, aircraft, source, destination, date, departure_time, arrival_time, price, total_seats, available_seats)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', all_flights)
        conn.commit()
        print(f"✅ Added {count} flights successfully")
        return True
    except Exception as e:
        print(f"❌ Error generating flights: {e}")
        return False
