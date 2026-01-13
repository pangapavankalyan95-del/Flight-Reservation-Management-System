from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

DATABASE = 'flight_reservation.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not name or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
            ''', (name, email, password_hash))
            conn.commit()
            user_id = cursor.lastrowid
            
            # Create session
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_email'] = email
            session['is_admin'] = 0
            
            return jsonify({
                'message': 'Registration successful',
                'user': {'id': user_id, 'name': name, 'email': email}
            }), 201
            
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email already registered'}), 400
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['is_admin'] = user['is_admin']
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['user_id'],
                    'name': user['name'],
                    'email': user['email'],
                    'is_admin': user['is_admin']
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['GET'])
def logout():
    """User logout"""
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'name': session['user_name'],
                'email': session['user_email'],
                'is_admin': session.get('is_admin', 0)
            }
        }), 200
    else:
        return jsonify({'authenticated': False}), 200

# ==================== FLIGHT ROUTES ====================

@app.route('/api/flights/search', methods=['GET'])
def search_flights():
    """Search flights by source, destination, and date"""
    try:
        source = request.args.get('source', '').strip()
        destination = request.args.get('destination', '').strip()
        date = request.args.get('date', '').strip()
        
        if not source or not destination or not date:
            return jsonify({'error': 'Source, destination, and date are required'}), 400
        
        # Real-time filtering logic
        current_date_str = datetime.now().strftime('%Y-%m-%d')
        current_time_str = datetime.now().strftime('%H:%M')
        
        # Block past dates completely (extra safety)
        if date < current_date_str:
             return jsonify({'flights': []}), 200

        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM flights
            WHERE LOWER(source) LIKE LOWER(?)
            AND LOWER(destination) LIKE LOWER(?)
            AND date = ?
            AND available_seats > 0
        '''
        params = [f'%{source}%', f'%{destination}%', date]
        
        # If searching for today, only show future flights
        if date == current_date_str:
            query += ' AND departure_time > ?'
            params.append(current_time_str)
            
        query += ' ORDER BY departure_time'
        
        cursor.execute(query, tuple(params))
        
        flights = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'flights': flights}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/flights', methods=['GET', 'POST'])
def manage_flights():
    """Get all flights or add new flight (admin only)"""
    
    if request.method == 'GET':
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM flights ORDER BY date, departure_time')
            flights = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return jsonify({'flights': flights}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        # Check admin authentication
        if not session.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403
        
        try:
            data = request.get_json()
            
            # Validation
            required_fields = ['flight_number', 'source', 'destination', 'date', 
                             'departure_time', 'arrival_time', 'price', 'total_seats']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field} is required'}), 400
            
            conn = get_db()
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO flights (flight_number, source, destination, date, 
                                       departure_time, arrival_time, price, total_seats, available_seats)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['flight_number'],
                    data['source'],
                    data['destination'],
                    data['date'],
                    data['departure_time'],
                    data['arrival_time'],
                    data['price'],
                    data['total_seats'],
                    data['total_seats']  # Initially all seats are available
                ))
                conn.commit()
                flight_id = cursor.lastrowid
                
                return jsonify({
                    'message': 'Flight added successfully',
                    'flight_id': flight_id
                }), 201
                
            except sqlite3.IntegrityError:
                return jsonify({'error': 'Flight number already exists'}), 400
            finally:
                conn.close()
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# ==================== BOOKING ROUTES ====================

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """Create a new booking with seat availability check"""
    
    # Check authentication
    if 'user_id' not in session:
        return jsonify({'error': 'Please login to book flights'}), 401
    
    try:
        data = request.get_json()
        flight_id = data.get('flight_id')
        seats_booked = data.get('seats_booked')
        passenger_names = data.get('passenger_names', '')
        booking_class = data.get('booking_class', 'Economy')
        seat_numbers = data.get('seat_numbers', '')
        
        # Validation
        if not flight_id or not seats_booked:
            return jsonify({'error': 'Flight ID and number of seats are required'}), 400
        
        if seats_booked < 1:
            return jsonify({'error': 'At least 1 seat must be booked'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get flight details and check seat availability
        cursor.execute('SELECT * FROM flights WHERE flight_id = ?', (flight_id,))
        flight = cursor.fetchone()
        
        if not flight:
            conn.close()
            return jsonify({'error': 'Flight not found'}), 404
        
        # SEAT AVAILABILITY LOGIC
        if flight['available_seats'] < seats_booked:
            conn.close()
            return jsonify({
                'error': f'Not enough seats available. Only {flight["available_seats"]} seats remaining'
            }), 400
        
        # Calculate total price with class multiplier
        multiplier = 1.0
        if booking_class == 'Business': multiplier = 2.5
        elif booking_class == 'First': multiplier = 4.0
        
        total_price = (flight['price'] * multiplier) * seats_booked
        
        # Create booking
        cursor.execute('''
            INSERT INTO bookings (user_id, flight_id, seats_booked, passenger_names, total_price, booking_class, seat_numbers)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], flight_id, seats_booked, passenger_names, total_price, booking_class, seat_numbers))
        
        booking_id = cursor.lastrowid
        
        # Update available seats
        new_available_seats = flight['available_seats'] - seats_booked
        cursor.execute('''
            UPDATE flights
            SET available_seats = ?
            WHERE flight_id = ?
        ''', (new_available_seats, flight_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Booking confirmed successfully',
            'booking_id': booking_id,
            'total_price': total_price,
            'seats_booked': seats_booked
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings/history', methods=['GET'])
def booking_history():
    """Get user's booking history"""
    
    # Check authentication
    if 'user_id' not in session:
        return jsonify({'error': 'Please login to view bookings'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # SELECT * returns all updated columns including booking_class and seat_numbers
        cursor.execute('''
            SELECT b.*, f.flight_number, f.source, f.destination, f.date, 
                   f.departure_time, f.arrival_time
            FROM bookings b
            JOIN flights f ON b.flight_id = f.flight_id
            WHERE b.user_id = ?
            ORDER BY b.booking_date DESC
        ''', (session['user_id'],))
        
        bookings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'bookings': bookings}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== PAGE ROUTES ====================

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    """Signup page"""
    return render_template('signup.html')

@app.route('/bookings')
def bookings_page():
    """Bookings page"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('bookings.html')

@app.route('/admin')
def admin_page():
    """Admin page"""
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    return render_template('admin.html')

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    if not os.path.exists(DATABASE):
        print("Database not found. Please run 'python init_db.py' first.")
    else:
        # Maintain flight pool
        try:
            from flight_utils import generate_flights
            conn = get_db()
            cursor = conn.cursor()
            
            # Optional: Clear very old flights (e.g., older than yesterday) to keep DB clean
            # cursor.execute("DELETE FROM flights WHERE date < date('now', '-1 day')")
            # conn.commit()
            
            # Count valid future flights
            cursor.execute("SELECT COUNT(*) FROM flights WHERE date >= date('now')")
            count = cursor.fetchone()[0]
            print(f"✈️ Current valid flights: {count}")
            
            if count < 500:
                needed = 500 - count
                print(f"⚠️ Flight pool low. Generering {needed} new flights...")
                generate_flights(conn, needed)
            
            conn.close()
        except Exception as e:
            print(f"Server Startup Warning: Could not maintain flight pool: {e}")

    app.run(debug=True, host='0.0.0.0', port=5000)
