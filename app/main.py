from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Patient, Appointment, User, AppointmentStatus
from datetime import datetime, timedelta
from sqlalchemy import func, Date
bp = Blueprint('main', __name__)
@bp.route('/')
@login_required
def dashboard():
    # Get today's date
    today = datetime.now().date()

    todays_query = Appointment.query.filter(func.cast(Appointment.date_time, Date) == today)
    pending_query = Appointment.query.filter(Appointment.status == AppointmentStatus.pending)

    if not current_user.can('admin.access') and current_user.can('clinical.view_own'):
        todays_query = todays_query.filter(Appointment.doctor_id == current_user.id)
        pending_query = pending_query.filter(Appointment.doctor_id == current_user.id)

    todays_appointments = todays_query.order_by(Appointment.date_time).all()
    today_appointments_count = todays_query.count()
    pending_appointments_count = pending_query.count()

    # Statistics
    total_patients = Patient.query.count()

    today_appointments = Appointment.query.filter(
        func.cast(Appointment.date_time, Date) == today
    ).count()

    pending_appointments = Appointment.query.filter(
        Appointment.status == AppointmentStatus.pending
    ).count()

    # Recent patients (last 5)
    recent_patients = Patient.query.order_by(
        Patient.created_at.desc()
    ).limit(5).all()

    # Today's appointments
    todays_appointments = Appointment.query.filter(
        func.cast(Appointment.date_time, Date) == today
    ).order_by(Appointment.date_time).all()

    # Doctor-specific view
    if not current_user.can('admin.access'):
        todays_appointments = [
            appt for appt in todays_appointments
            if appt.doctor_id == current_user.id
        ]

    if current_user.can('clinical.view_own') and not current_user.can('admin.access'):
        return redirect(url_for('clinical.doctor_dashboard'))

    # Get today's date
    today = datetime.now().date()

    # Statistics
    total_patients = Patient.query.count()

    today_appointments = Appointment.query.filter(
        func.cast(Appointment.date_time, Date) == today
    ).count()

    pending_appointments = Appointment.query.filter(
        Appointment.status == AppointmentStatus.pending
    ).count()

    # Recent patients (last 5)
    recent_patients = Patient.query.order_by(
        Patient.created_at.desc()
    ).limit(5).all()

    # Today's appointments
    todays_appointments = Appointment.query.filter(
        func.cast(Appointment.date_time, Date) == today
    ).order_by(Appointment.date_time).all()

    return render_template(
        'dashboard.html',
        total_patients=total_patients,
        today_appointments=today_appointments_count,
        pending_appointments=pending_appointments_count,
        recent_patients=recent_patients,
        todays_appointments=todays_appointments
    )
