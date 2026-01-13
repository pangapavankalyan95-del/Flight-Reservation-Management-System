# ✈️ Flight Reservation Management System

A premium, full-stack web application designed for seamless flight discovery and booking. Built with a focus on user experience, real-time data integrity, and administrative control.

![Project Preview](https://img.shields.io/badge/Status-Live-success)
![Python](https://img.shields.io/badge/Backend-Python_3.8+-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey)

## 🌟 Key Features

### 🔍 Smart Flight Discovery
- **Dynamic Search:** Find flights by source, destination, and date with instant results.
- **Advanced Filtering:** Narrow down options by price range, departure time (Morning/Afternoon/Evening), and sorting (Price, Time).
- **Real-time Availability:** Integrated logic ensures only future flights with available seats are displayed.

### 🎟️ Booking Wizard
- **Multi-Seat Selection:** Select up to 5 seats for standard bookings or up to 10 for group bookings.
- **Interactive Seat Map:** Visual seat selection with real-time status (Available, Selected, Occupied).
- **Class Options:** Choose between Economy, Business, and First Class with dynamic pricing multipliers.
- **Passenger Management:** Individual name entry for every seat booked in a single transaction.

### ⚙️ Automated Flight Management
- **Intelligent Flight Pool:** Automatically maintains a minimum of 500 valid future flights using a realistic generation engine (Airlines like Air India, Emirates, Lufthansa, etc.).
- **Data Integrity:** Automatic cleanup of past flights to keep the database lean and relevant.

### 🔐 Security & Auth
- **Secure Authentication:** Password hashing using `werkzeug` for maximum security.
- **Role-based Access:** Dedicated Administrative dashboard for flight management.

## 🛠️ Tech Stack

- **Backend:** Python Flask
- **Frontend:** Vanilla CSS (Glassmorphism), JavaScript (Async/Fetch), Bootstrap 5
- **Database:** SQLite (Relational DB)
- **Deployment:** Render

## 🚀 Local Setup

### 1. Clone & Environment
```powershell
git clone https://github.com/pangapavankalyan95-del/Flight-Reservation-Management-System.git
cd "Flight-Reservation-Management-System"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install & Run
```powershell
pip install -r requirements.txt
python init_db.py  # Initializes database with 1500+ realistic flights
python app.py
```

## 🌐 Deploy to Render

1. **GitHub:** Push your code to your repository.
2. **New Web Service:** Select your repository on Render.
3. **Build Command:** `pip install -r requirements.txt && python init_db.py`
4. **Start Command:** `gunicorn app:app`

## 👨‍💻 Author
**Panga Pavan Kalyan**
[GitHub Profile](https://github.com/pangapavankalyan95-del)

---
*Created for portfolio demonstration purposes.*

