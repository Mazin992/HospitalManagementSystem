# Hospital Management System

A comprehensive web-based application built with Flask to manage hospital operations including patients, appointments, clinical records, bed admissions, billing, and user roles.
## Demo

[![Project Demo](https://img.youtube.com/vi/bNso-urXYiw/hqdefault.jpg)](https://www.youtube.com/watch?v=bNso-urXYiw)

Click the image above to watch the video on YouTube.

## ✨ Features

- **Patient Management**: Register, view, and manage patient records.
- **Appointment Scheduling**: Book, view, and manage doctor appointments.
- **Clinical Documentation**: Record medical visits, diagnoses, prescriptions, and vitals.
- **Bed & Admission Management**: Admit/discharge patients and track bed occupancy.
- **Billing & Invoicing**: Create invoices, manage medical services, and process payments.
- **Role-Based Access Control**: Granular permissions for roles like Doctor, Nurse, Receptionist, Billing Staff, and Admin.
- **Reporting & Analytics**: Dashboard with real-time stats on patients, appointments, revenue, and more.
- **Arabic RTL Support**: Fully localized interface with right-to-left layout.

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL (via SQLAlchemy)
- **Frontend**: HTML5, Bootstrap 5 (RTL), JavaScript
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF, WTForms
- **Deployment Ready**: Configurable for development and production

## 📦 Requirements

- Python 3.9+
- PostgreSQL
- `pip` for Python package management

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Mazin992/HospitalManagementSystem.git
   cd HospitalManagementSystem
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment (optional)**
   ```bash
   export FLASK_CONFIG=development
   ```

4. **Initialize the database**  
   Run the included initialization script:
   ```bash
   python preInstall/init_db.py
   ```

5. **Run the application**
   ```bash
   python run.py
   ```
   Visit `http://localhost:5000` in your browser.

## 🔐 Default Admin Account

After initialization, a default admin user is created:
- **Username**: `admin`
- **Password**: `admin` *(change after first login)*

## 📄 License

This project is for educational and demonstration purposes. Modify and distribute as needed.

---

> Developed by **Mazin Elfaki**  

> © 2026 Hospital Management System

