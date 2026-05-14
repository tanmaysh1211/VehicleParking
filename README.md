# 🚗 Vehicle Parking App

A Flask-based multi-user parking management system with separate Admin and User roles, SQLite database, and analytics charts.

---

## ✨ Features

### 👨‍💼 Admin
- Add, Edit, Delete parking lots
- View live spot occupancy per lot
- View all registered users
- Analytics dashboard with charts:
  - Occupied vs Free Spots
  - Total Income per Parking Lot

### 👤 User
- Register & Login
- Search parking lots by pincode or address
- Auto-allocate first available spot
- Release spot with live price preview
- View booking history (last 3)
- Weekly spending summary chart
- View invoice for completed bookings

---

## 🛠️ Tech Stack

| Layer       | Technology                     |
|-------------|--------------------------------|
| Backend     | Python, Flask, Flask-SQLAlchemy |
| Database    | SQLite                         |
| Frontend    | HTML, CSS, Jinja2              |
| Charts      | Matplotlib                     |

---

## 📂 Project Structure

```
vehicle-parking-app/
│
├── app.py                  # Main Flask app (models + routes)
├── requirements.txt
├── README.md
├── .gitignore
│
├── instance/
│   └── parking.db          # SQLite DB (auto-created, not pushed)
│
├── static/
│   └── style.css
│
└── templates/
    ├── landing.html
    ├── signup.html
    ├── edit_user.html
    ├── invoice.html
    ├── user_dashboard.html
    ├── user_summary.html
    ├── book_spot.html
    ├── release_spot.html
    ├── admin_dashboard.html
    ├── admin_summary.html
    ├── add_parking.html
    ├── edit_parking.html
    ├── view_parking.html
    └── view_users.html
```

---

## ⚙️ Setup & Run

```bash

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Visit: `http://127.0.0.1:5000`

---

## 🔐 Default Admin Login

| Field    | Value                          |
|----------|-------------------------------|
| Email    | sharma.tanmay4002@gmail.com   |
| Password | karan@0801                    |

> Admin account is auto-created on first run if none exists.

---

## 🧩 ER Model

### User
- id, email, password, name, address, pin_code, is_admin

### ParkingLot
- id, parking_lot_name, address, pin_code, price_per_hour, total_capacity, available_capacity

### ParkingSpot
- id, lot_id (FK), spot_number, is_occupied, user_id (FK), vehicle_number, start_time, end_time

### History
- id, user_id (FK), spot_id (FK), vehicle_number, start_time, end_time, total_time, total_price

---

## ⚠️ Notes

- One active booking per user at a time
- Lots with occupied spots cannot be deleted
- Date formatting uses `%d` (Windows-compatible, not `%-d`)
- SQLite DB is excluded from git via `.gitignore`