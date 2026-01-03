from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.clinical import bp
from app.clinical.forms import MedicalVisitForm
from app.models import Appointment, MedicalVisit, Patient, AppointmentStatus
from app.decorators import role_required
from app import db
from datetime import datetime, date
from sqlalchemy import func, desc

@bp.route('/doctor/dashboard')
@login_required
@role_required('Doctor', 'Super Admin')
def doctor_dashboard():
    """Doctor's personalized dashboard showing their appointments"""
    
    today = date.today()
    
    # Get doctor's appointments for today
    if current_user.role.name == 'Super Admin':
        # Super Admin can see all appointments
        todays_appointments = Appointment.query.filter(
            func.date(Appointment.date_time) == today
        ).order_by(Appointment.date_time).all()
        
        pending_appointments = Appointment.query.filter(
            Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed])
        ).count()
    else:
        # Regular doctors see only their appointments
        todays_appointments = Appointment.query.filter(
            Appointment.doctor_id == current_user.id,
            func.date(Appointment.date_time) == today
        ).order_by(Appointment.date_time).all()
        
        pending_appointments = Appointment.query.filter(
            Appointment.doctor_id == current_user.id,
            Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed])
        ).count()
    
    # Upcoming appointments (next 7 days, excluding today)
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date_time > datetime.now(),
        func.date(Appointment.date_time) > today,
        Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed])
    ).order_by(Appointment.date_time).limit(10).all()
    
    # Recent completed visits
    recent_visits = MedicalVisit.query.filter(
        MedicalVisit.doctor_id == current_user.id
    ).order_by(desc(MedicalVisit.created_at)).limit(5).all()
    
    # Statistics
    completed_today = sum(1 for appt in todays_appointments if appt.status == AppointmentStatus.completed)
    total_today = len(todays_appointments)
    
    return render_template(
        'clinical/doctor_dashboard.html',
        todays_appointments=todays_appointments,
        upcoming_appointments=upcoming_appointments,
        recent_visits=recent_visits,
        pending_appointments=pending_appointments,
        completed_today=completed_today,
        total_today=total_today
    )


@bp.route('/doctor/visit/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@role_required('Doctor', 'Super Admin')
def consultation(appointment_id):
    """Consultation page for entering medical visit details"""
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify doctor owns this appointment (unless Super Admin)
    if current_user.role.name != 'Super Admin':
        if appointment.doctor_id != current_user.id:
            flash('ليس لديك صلاحية للوصول إلى هذا الموعد.', 'danger')
            return redirect(url_for('clinical.doctor_dashboard'))
    
    # Check if visit already exists
    existing_visit = MedicalVisit.query.filter_by(appointment_id=appointment_id).first()
    
    if existing_visit and request.method == 'GET':
        flash('تم إنهاء هذا الكشف مسبقاً. يمكنك عرض التفاصيل أدناه.', 'info')
        return redirect(url_for('clinical.view_visit', visit_id=existing_visit.id))
    
    form = MedicalVisitForm()
    
    # Get patient's previous visits for reference
    previous_visits = MedicalVisit.query.join(Appointment).filter(
        Appointment.patient_id == appointment.patient_id,
        MedicalVisit.id != (existing_visit.id if existing_visit else 0)
    ).order_by(desc(MedicalVisit.created_at)).limit(5).all()
    
    if form.validate_on_submit():
        # Prepare vitals JSON
        vitals = {}
        if form.temperature.data:
            vitals['temperature'] = float(form.temperature.data)
        if form.blood_pressure.data:
            vitals['blood_pressure'] = form.blood_pressure.data.strip()
        if form.heart_rate.data:
            vitals['heart_rate'] = float(form.heart_rate.data)
        if form.weight.data:
            vitals['weight'] = float(form.weight.data)
        if form.height.data:
            vitals['height'] = float(form.height.data)
        if form.notes.data:
            vitals['notes'] = form.notes.data.strip()
        
        if existing_visit:
            # Update existing visit
            existing_visit.symptoms = form.symptoms.data.strip()
            existing_visit.diagnosis = form.diagnosis.data.strip()
            existing_visit.prescription_text = form.prescription_text.data.strip() if form.prescription_text.data else None
            existing_visit.vitals = vitals if vitals else None
            
            flash('تم تحديث بيانات الكشف بنجاح.', 'success')
        else:
            # Create new visit
            visit = MedicalVisit(
                appointment_id=appointment_id,
                doctor_id=current_user.id,
                symptoms=form.symptoms.data.strip(),
                diagnosis=form.diagnosis.data.strip(),
                prescription_text=form.prescription_text.data.strip() if form.prescription_text.data else None,
                vitals=vitals if vitals else None
            )
            db.session.add(visit)
            
            # Update appointment status to completed
            appointment.status = AppointmentStatus.completed
            
            flash('تم حفظ الكشف الطبي بنجاح وتم إنهاء الموعد.', 'success')
        
        try:
            db.session.commit()
            return redirect(url_for('clinical.doctor_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء حفظ البيانات. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template(
        'clinical/consultation.html',
        form=form,
        appointment=appointment,
        patient=appointment.patient,
        previous_visits=previous_visits,
        existing_visit=existing_visit
    )


@bp.route('/doctor/visit/view/<int:visit_id>')
@login_required
@role_required('Doctor', 'Super Admin', 'Nurse', 'Reception')
def view_visit(visit_id):
    """View a completed medical visit (read-only)"""
    
    visit = MedicalVisit.query.get_or_404(visit_id)
    
    # Doctors can only view their own visits (unless Super Admin)
    if current_user.role.name == 'Doctor':
        if visit.doctor_id != current_user.id:
            flash('ليس لديك صلاحية لعرض هذا الكشف.', 'danger')
            return redirect(url_for('clinical.doctor_dashboard'))
    
    return render_template('clinical/view_visit.html', visit=visit)


@bp.route('/patient/<int:patient_id>/history')
@login_required
@role_required('Doctor', 'Super Admin', 'Nurse', 'Reception')
def patient_history(patient_id):
    """View patient's complete medical history"""
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Get all medical visits for this patient
    visits = MedicalVisit.query.join(Appointment).filter(
        Appointment.patient_id == patient_id
    ).order_by(desc(MedicalVisit.created_at)).all()
    
    # Get all appointments (including those without visits)
    appointments = Appointment.query.filter(
        Appointment.patient_id == patient_id
    ).order_by(desc(Appointment.date_time)).all()
    
    return render_template(
        'clinical/patient_history.html',
        patient=patient,
        visits=visits,
        appointments=appointments
    )


@bp.route('/doctor/appointment/<int:appointment_id>/start', methods=['POST'])
@login_required
@role_required('Doctor', 'Super Admin')
def start_appointment(appointment_id):
    """Mark appointment as in-progress and redirect to consultation"""
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if current_user.role.name != 'Super Admin':
        if appointment.doctor_id != current_user.id:
            flash('ليس لديك صلاحية لهذا الإجراء.', 'danger')
            return redirect(url_for('clinical.doctor_dashboard'))
    
    # Update status if pending or confirmed
    if appointment.status in [AppointmentStatus.pending, AppointmentStatus.confirmed]:
        appointment.status = AppointmentStatus.confirmed
        db.session.commit()
    
    return redirect(url_for('clinical.consultation', appointment_id=appointment_id))


@bp.route('/doctor/appointment/<int:appointment_id>/no-show', methods=['POST'])
@login_required
@role_required('Doctor', 'Super Admin')
def mark_no_show(appointment_id):
    """Mark appointment as no-show"""
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if current_user.role.name != 'Super Admin':
        if appointment.doctor_id != current_user.id:
            flash('ليس لديك صلاحية لهذا الإجراء.', 'danger')
            return redirect(url_for('clinical.doctor_dashboard'))
    
    appointment.status = AppointmentStatus.no_show
    
    try:
        db.session.commit()
        flash('تم تسجيل المريض كـ "لم يحضر".', 'info')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ. يرجى المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('clinical.doctor_dashboard'))