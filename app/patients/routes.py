
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.patients import bp
from app.patients.forms import PatientForm, PatientSearchForm
from app.models import Patient
from app.decorators import permission_required
from app import db
from datetime import datetime
import random
import string

def generate_file_number():
    """Generate unique patient file number (Format: P-YYYYMMDD-XXXX)"""
    date_str = datetime.now().strftime('%Y%m%d')
    
    while True:
        random_suffix = ''.join(random.choices(string.digits, k=4))
        file_number = f'P-{date_str}-{random_suffix}'
        
        # Check if file number exists
        existing = Patient.query.filter_by(file_number=file_number).first()
        if not existing:
            return file_number


@bp.route('/')
@login_required
@permission_required('patients', 'read')
def list_patients():
    """List all patients with search functionality"""
    search_form = PatientSearchForm()
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # Base query
    query = Patient.query
    
    # Search functionality
    search_query = request.args.get('search_query', '').strip()
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Patient.full_name.ilike(search_pattern),
                Patient.phone.ilike(search_pattern),
                Patient.file_number.ilike(search_pattern)
            )
        )
    
    # Pagination
    patients = query.order_by(Patient.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'patients/list.html',
        patients=patients,
        search_form=search_form,
        search_query=search_query
    )


@bp.route('/new', methods=['GET', 'POST'])
@login_required
@permission_required('patients', 'write')
def create_patient():
    """Register new patient"""
    form = PatientForm()
    
    if form.validate_on_submit():
        # Generate unique file number
        file_number = generate_file_number()
        
        patient = Patient(
            file_number=file_number,
            full_name=form.full_name.data.strip(),
            phone=form.phone.data.strip(),
            gender=form.gender.data if form.gender.data else None,
            dob=form.dob.data,
            address=form.address.data.strip() if form.address.data else None,
            emergency_contact=form.emergency_contact.data.strip() if form.emergency_contact.data else None
        )
        
        try:
            db.session.add(patient)
            db.session.commit()
            flash(f'تم تسجيل المريض بنجاح. رقم الملف: {file_number}', 'success')
            return redirect(url_for('patients.view_patient', patient_id=patient.id))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء التسجيل. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('patients/create.html', form=form)


@bp.route('/<int:patient_id>')
@login_required
@permission_required('patients', 'read')
def view_patient(patient_id):
    """View patient details"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Get recent appointments
    recent_appointments = patient.appointments.order_by(
        db.desc('date_time')
    ).limit(10).all()
    
    # Get active admissions
    active_admissions = patient.admissions.filter_by(status='active').all()
    
    # Get recent invoices
    recent_invoices = patient.invoices.order_by(
        db.desc('created_at')
    ).limit(5).all()
    
    return render_template(
        'patients/view.html',
        patient=patient,
        recent_appointments=recent_appointments,
        active_admissions=active_admissions,
        recent_invoices=recent_invoices
    )


@bp.route('/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('patients', 'write')
def edit_patient(patient_id):
    """Edit patient information"""
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    
    if form.validate_on_submit():
        patient.full_name = form.full_name.data.strip()
        patient.phone = form.phone.data.strip()
        patient.gender = form.gender.data if form.gender.data else None
        patient.dob = form.dob.data
        patient.address = form.address.data.strip() if form.address.data else None
        patient.emergency_contact = form.emergency_contact.data.strip() if form.emergency_contact.data else None
        
        try:
            db.session.commit()
            flash('تم تحديث بيانات المريض بنجاح.', 'success')
            return redirect(url_for('patients.view_patient', patient_id=patient.id))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء التحديث. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('patients/edit.html', form=form, patient=patient)


@bp.route('/<int:patient_id>/delete', methods=['POST'])
@login_required
@permission_required('patients', 'delete')
def delete_patient(patient_id):
    """Delete patient (soft delete by checking dependencies)"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if patient has any appointments, admissions, or invoices
    if patient.appointments.count() > 0:
        flash('لا يمكن حذف المريض. يوجد مواعيد مسجلة.', 'warning')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))
    
    if patient.admissions.count() > 0:
        flash('لا يمكن حذف المريض. يوجد سجلات إقامة.', 'warning')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))
    
    if patient.invoices.count() > 0:
        flash('لا يمكن حذف المريض. يوجد فواتير مسجلة.', 'warning')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))
    
    try:
        db.session.delete(patient)
        db.session.commit()
        flash('تم حذف المريض بنجاح.', 'success')
        return redirect(url_for('patients.list_patients'))
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء الحذف. يرجى المحاولة مرة أخرى.', 'danger')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))
