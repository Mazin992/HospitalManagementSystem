from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.appointments import bp
from app.appointments.forms import AppointmentForm, QuickAppointmentForm
from app.models import Appointment, Patient, User, AppointmentStatus
from app.decorators import permission_required
from app import db
from datetime import datetime, timedelta
from sqlalchemy import and_, Date

def check_doctor_availability(doctor_id, date_time, exclude_appointment_id=None):
    """
    Check if doctor has conflicting appointments
    Returns (is_available, conflicting_appointment)
    """
    # Check for appointments within 30 minutes window
    time_window_start = date_time - timedelta(minutes=30)
    time_window_end = date_time + timedelta(minutes=30)
    
    query = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date_time.between(time_window_start, time_window_end),
        Appointment.status.in_([
            AppointmentStatus.pending,
            AppointmentStatus.confirmed
        ])
    )
    
    # Exclude current appointment if editing
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    
    conflicting = query.first()
    
    return (conflicting is None, conflicting)


@bp.route('/')
@login_required
@permission_required('appointments', 'read')
def list_appointments():
    """List all appointments with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filter parameters
    status_filter = request.args.get('status', 'all')
    doctor_filter = request.args.get('doctor_id', 0, type=int)
    date_filter = request.args.get('date', '')
    
    # Base query
    query = Appointment.query
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter(Appointment.status == AppointmentStatus[status_filter])
    
    if doctor_filter > 0:
        query = query.filter(Appointment.doctor_id == doctor_filter)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(db.func.cast(Appointment.date_time, Date) == filter_date)
        except ValueError:
            pass
    
    # Pagination
    appointments = query.order_by(Appointment.date_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get all doctors for filter dropdown
    doctors = User.query.join(User.role).filter(
        db.text("roles.name IN ('Doctor', 'Super Admin')")
    ).filter(User.is_active == True).all()
    
    return render_template(
        'appointments/list.html',
        appointments=appointments,
        doctors=doctors,
        status_filter=status_filter,
        doctor_filter=doctor_filter,
        date_filter=date_filter
    )


@bp.route('/book', methods=['GET', 'POST'])
@login_required
@permission_required('appointments', 'write')
def book_appointment():
    """Book new appointment"""
    # Check if patient_id is provided in query params
    patient_id = request.args.get('patient_id', type=int)
    
    if patient_id:
        # Quick booking for specific patient
        patient = Patient.query.get_or_404(patient_id)
        form = QuickAppointmentForm()
        
        # Populate doctor choices
        doctors = User.query.join(User.role).filter(
            db.text("roles.name IN ('Doctor', 'Super Admin')")
        ).filter(User.is_active == True).all()
        form.doctor_id.choices = [(0, 'اختر الطبيب')] + [
            (d.id, d.full_name_ar) for d in doctors
        ]
        
        if form.validate_on_submit():
            # Check doctor availability
            is_available, conflicting = check_doctor_availability(
                form.doctor_id.data,
                form.date_time.data
            )
            
            if not is_available:
                flash(
                    f'الطبيب لديه موعد آخر في {conflicting.date_time.strftime("%Y-%m-%d %H:%M")}. '
                    'يرجى اختيار وقت آخر.',
                    'warning'
                )
                return render_template('appointments/book.html', form=form, patient=patient)
            
            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=form.doctor_id.data,
                date_time=form.date_time.data,
                type=form.type.data,
                notes=form.notes.data,
                status=AppointmentStatus.confirmed
            )
            
            try:
                db.session.add(appointment)
                db.session.commit()
                flash('تم حجز الموعد بنجاح.', 'success')
                return redirect(url_for('patients.view_patient', patient_id=patient_id))
            except Exception as e:
                db.session.rollback()
                flash('حدث خطأ أثناء الحجز. يرجى المحاولة مرة أخرى.', 'danger')
        
        return render_template('appointments/book.html', form=form, patient=patient)
    
    else:
        # Regular booking form
        form = AppointmentForm()
        
        if form.validate_on_submit():
            # Check doctor availability
            is_available, conflicting = check_doctor_availability(
                form.doctor_id.data,
                form.date_time.data
            )
            
            if not is_available:
                flash(
                    f'الطبيب لديه موعد آخر في {conflicting.date_time.strftime("%Y-%m-%d %H:%M")}. '
                    'يرجى اختيار وقت آخر.',
                    'warning'
                )
                return render_template('appointments/book.html', form=form)
            
            appointment = Appointment(
                patient_id=form.patient_id.data,
                doctor_id=form.doctor_id.data,
                date_time=form.date_time.data,
                type=form.type.data,
                notes=form.notes.data,
                status=AppointmentStatus.confirmed
            )
            
            try:
                db.session.add(appointment)
                db.session.commit()
                flash('تم حجز الموعد بنجاح.', 'success')
                return redirect(url_for('appointments.view_appointment', appointment_id=appointment.id))
            except Exception as e:
                db.session.rollback()
                flash('حدث خطأ أثناء الحجز. يرجى المحاولة مرة أخرى.', 'danger')
        
        return render_template('appointments/book.html', form=form)


@bp.route('/<int:appointment_id>')
@login_required
@permission_required('appointments', 'read')
def view_appointment(appointment_id):
    """View appointment details"""
    appointment = Appointment.query.get_or_404(appointment_id)
    return render_template('appointments/view.html', appointment=appointment)


@bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@permission_required('appointments', 'write')
def cancel_appointment(appointment_id):
    """Cancel appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.status == AppointmentStatus.completed:
        flash('لا يمكن إلغاء موعد منتهي.', 'warning')
        return redirect(url_for('appointments.view_appointment', appointment_id=appointment_id))
    
    appointment.status = AppointmentStatus.cancelled
    
    try:
        db.session.commit()
        flash('تم إلغاء الموعد بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء الإلغاء. يرجى المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('appointments.view_appointment', appointment_id=appointment_id))


@bp.route('/api/check-availability', methods=['POST'])
@login_required
def check_availability():
    """API endpoint to check doctor availability"""
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    date_time_str = data.get('date_time')
    
    if not doctor_id or not date_time_str:
        return jsonify({'available': False, 'message': 'بيانات غير كاملة'})
    
    try:
        date_time = datetime.fromisoformat(date_time_str)
        is_available, conflicting = check_doctor_availability(doctor_id, date_time)
        
        if is_available:
            return jsonify({'available': True})
        else:
            return jsonify({
                'available': False,
                'message': f'الطبيب لديه موعد آخر في {conflicting.date_time.strftime("%Y-%m-%d %H:%M")}'
            })
    except Exception as e:
        return jsonify({'available': False, 'message': 'حدث خطأ في التحقق'})