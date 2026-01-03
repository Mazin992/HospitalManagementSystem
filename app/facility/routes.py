from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.facility import bp
from app.facility.forms import AdmitPatientForm, DischargePatientForm, BedStatusForm
from app.models import Bed, Admission, Patient, BedStatus, AdmissionStatus
from app.decorators import role_required, permission_required
from app import db
from datetime import datetime
from sqlalchemy import func, and_

@bp.route('/beds')
@login_required
@role_required('Nurse', 'Super Admin', 'Reception')
def beds_list():
    """View all beds with their current status"""
    
    # Group beds by room
    rooms = {}
    all_beds = Bed.query.order_by(Bed.room_number, Bed.bed_label).all()
    
    for bed in all_beds:
        if bed.room_number not in rooms:
            rooms[bed.room_number] = []
        rooms[bed.room_number].append(bed)
    
    # Statistics
    total_beds = len(all_beds)
    available_beds = sum(1 for b in all_beds if b.status == BedStatus.available)
    occupied_beds = sum(1 for b in all_beds if b.status == BedStatus.occupied)
    maintenance_beds = sum(1 for b in all_beds if b.status == BedStatus.maintenance)
    
    # Get current admissions for occupied beds
    active_admissions = Admission.query.filter_by(status=AdmissionStatus.active).all()
    admission_map = {adm.bed_id: adm for adm in active_admissions}
    
    return render_template(
        'facility/beds_list.html',
        rooms=rooms,
        total_beds=total_beds,
        available_beds=available_beds,
        occupied_beds=occupied_beds,
        maintenance_beds=maintenance_beds,
        admission_map=admission_map
    )


@bp.route('/bed/<int:bed_id>')
@login_required
@role_required('Nurse', 'Super Admin', 'Reception', 'Doctor')
def bed_detail(bed_id):
    """View detailed information about a specific bed"""
    
    bed = Bed.query.get_or_404(bed_id)
    
    # Get admission history for this bed
    admissions = Admission.query.filter_by(bed_id=bed_id).order_by(
        Admission.admission_date.desc()
    ).limit(10).all()
    
    # Get current admission if occupied
    current_admission = None
    if bed.status == BedStatus.occupied:
        current_admission = Admission.query.filter_by(
            bed_id=bed_id,
            status=AdmissionStatus.active
        ).first()
    
    return render_template(
        'facility/bed_detail.html',
        bed=bed,
        admissions=admissions,
        current_admission=current_admission
    )


@bp.route('/bed/<int:bed_id>/status', methods=['GET', 'POST'])
@login_required
@role_required('Nurse', 'Super Admin')
def change_bed_status(bed_id):
    """Manually change bed status (only for available/maintenance)"""
    
    bed = Bed.query.get_or_404(bed_id)
    
    # Cannot change status if occupied
    if bed.status == BedStatus.occupied:
        flash('لا يمكن تغيير حالة السرير المشغول. يجب تسجيل خروج المريض أولاً.', 'danger')
        return redirect(url_for('facility.bed_detail', bed_id=bed_id))
    
    form = BedStatusForm()
    
    if form.validate_on_submit():
        old_status = bed.status.value
        bed.status = BedStatus[form.status.data]
        
        try:
            db.session.commit()
            flash(f'تم تحديث حالة السرير من "{old_status}" إلى "{bed.status.value}".', 'success')
            return redirect(url_for('facility.beds_list'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء التحديث. يرجى المحاولة مرة أخرى.', 'danger')
    
    # Pre-fill with current status if not occupied
    if request.method == 'GET':
        form.status.data = bed.status.value
    
    return render_template('facility/change_bed_status.html', form=form, bed=bed)


@bp.route('/admissions')
@login_required
@role_required('Nurse', 'Super Admin', 'Doctor', 'Reception')
def admissions_list():
    """View all admissions with filters"""
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'active')
    
    # Base query
    query = Admission.query
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter_by(status=AdmissionStatus.active)
    elif status_filter == 'discharged':
        query = query.filter_by(status=AdmissionStatus.discharged)
    
    # Pagination
    admissions = query.order_by(Admission.admission_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistics
    active_count = Admission.query.filter_by(status=AdmissionStatus.active).count()
    discharged_count = Admission.query.filter_by(status=AdmissionStatus.discharged).count()
    
    return render_template(
        'facility/admissions_list.html',
        admissions=admissions,
        status_filter=status_filter,
        active_count=active_count,
        discharged_count=discharged_count
    )


@bp.route('/admissions/admit', methods=['GET', 'POST'])
@login_required
@role_required('Nurse', 'Super Admin')
def admit_patient():
    """Admit a patient to a bed"""
    
    form = AdmitPatientForm()
    
    if form.validate_on_submit():
        patient_id = form.patient_id.data
        bed_id = form.bed_id.data
        
        # Validate patient
        patient = Patient.query.get(patient_id)
        if not patient:
            flash('المريض غير موجود.', 'danger')
            return redirect(url_for('facility.admit_patient'))
        
        # Check if patient already has active admission
        existing_admission = Admission.query.filter_by(
            patient_id=patient_id,
            status=AdmissionStatus.active
        ).first()
        
        if existing_admission:
            flash(f'المريض لديه إدخال نشط في غرفة {existing_admission.bed.room_number} - سرير {existing_admission.bed.bed_label}.', 'danger')
            return redirect(url_for('facility.admit_patient'))
        
        # Validate bed
        bed = Bed.query.get(bed_id)
        if not bed:
            flash('السرير غير موجود.', 'danger')
            return redirect(url_for('facility.admit_patient'))
        
        # Check if bed is available
        if bed.status != BedStatus.available:
            flash(f'السرير غير متاح. الحالة الحالية: {bed.status.value}', 'danger')
            return redirect(url_for('facility.admit_patient'))
        
        # Create admission record
        admission = Admission(
            patient_id=patient_id,
            bed_id=bed_id,
            admission_date=form.admission_date.data,
            status=AdmissionStatus.active,
            notes=form.notes.data.strip() if form.notes.data else None
        )
        
        # Update bed status to occupied
        bed.status = BedStatus.occupied
        
        try:
            db.session.add(admission)
            db.session.commit()
            flash(
                f'تم إدخال المريض {patient.full_name} إلى غرفة {bed.room_number} - سرير {bed.bed_label} بنجاح.',
                'success'
            )
            return redirect(url_for('facility.admissions_list'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء الإدخال. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('facility/admit_patient.html', form=form)


@bp.route('/admissions/<int:admission_id>')
@login_required
@role_required('Nurse', 'Super Admin', 'Doctor', 'Reception')
def admission_detail(admission_id):
    """View admission details"""
    
    admission = Admission.query.get_or_404(admission_id)
    
    return render_template('facility/admission_detail.html', admission=admission)


@bp.route('/admissions/<int:admission_id>/discharge', methods=['GET', 'POST'])
@login_required
@role_required('Nurse', 'Super Admin')
def discharge_patient(admission_id):
    """Discharge a patient from the hospital"""
    
    admission = Admission.query.get_or_404(admission_id)
    
    # Check if already discharged
    if admission.status == AdmissionStatus.discharged:
        flash('تم تسجيل خروج المريض مسبقاً.', 'info')
        return redirect(url_for('facility.admission_detail', admission_id=admission_id))
    
    form = DischargePatientForm()
    
    if form.validate_on_submit():
        # Validate discharge date is after admission date
        discharge_date = form.discharge_date.data
        if discharge_date < admission.admission_date:
            flash('تاريخ الخروج يجب أن يكون بعد تاريخ الدخول.', 'danger')
            return render_template('facility/discharge_patient.html', form=form, admission=admission)
        
        # Update admission
        admission.discharge_date = discharge_date
        admission.status = AdmissionStatus.discharged
        
        # Append discharge notes
        if form.notes.data:
            if admission.notes:
                admission.notes += f'\n\n[ملاحظات الخروج - {discharge_date.strftime("%Y-%m-%d %H:%M")}]\n{form.notes.data.strip()}'
            else:
                admission.notes = f'[ملاحظات الخروج]\n{form.notes.data.strip()}'
        
        # Update bed status to maintenance (needs cleaning)
        bed = admission.bed
        bed.status = BedStatus.maintenance
        
        try:
            db.session.commit()
            flash(
                f'تم تسجيل خروج المريض {admission.patient.full_name} بنجاح. السرير بحاجة للتنظيف.',
                'success'
            )
            return redirect(url_for('facility.admissions_list'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تسجيل الخروج. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('facility/discharge_patient.html', form=form, admission=admission)


@bp.route('/admissions/<int:admission_id>/quick-discharge', methods=['POST'])
@login_required
@role_required('Nurse', 'Super Admin')
def quick_discharge(admission_id):
    """Quick discharge with current timestamp"""
    
    admission = Admission.query.get_or_404(admission_id)
    
    if admission.status == AdmissionStatus.discharged:
        flash('تم تسجيل خروج المريض مسبقاً.', 'info')
        return redirect(url_for('facility.admissions_list'))
    
    # Discharge with current time
    admission.discharge_date = datetime.now()
    admission.status = AdmissionStatus.discharged
    
    # Update bed status to maintenance
    bed = admission.bed
    bed.status = BedStatus.maintenance
    
    try:
        db.session.commit()
        flash(f'تم تسجيل خروج المريض {admission.patient.full_name} بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ. يرجى المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('facility.admissions_list'))