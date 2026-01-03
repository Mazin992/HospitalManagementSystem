from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, DateTimeLocalField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional
from app.models import Patient, Bed, BedStatus
from datetime import datetime

class AdmitPatientForm(FlaskForm):
    patient_id = SelectField(
        'المريض',
        coerce=int,
        validators=[DataRequired(message='يرجى اختيار المريض')]
    )
    
    bed_id = SelectField(
        'السرير',
        coerce=int,
        validators=[DataRequired(message='يرجى اختيار السرير')]
    )
    
    admission_date = DateTimeLocalField(
        'تاريخ ووقت الإدخال',
        format='%Y-%m-%dT%H:%M',
        default=datetime.now,
        validators=[DataRequired(message='التاريخ والوقت مطلوبان')]
    )
    
    notes = TextAreaField(
        'ملاحظات',
        validators=[Optional()],
        render_kw={'rows': 4, 'placeholder': 'أي ملاحظات أو تعليمات خاصة...'}
    )
    
    submit = SubmitField('إدخال المريض')
    
    def __init__(self, *args, **kwargs):
        super(AdmitPatientForm, self).__init__(*args, **kwargs)
        
        # Get patients without active admissions
        from sqlalchemy import and_
        from app.models import Admission, AdmissionStatus
        
        active_patient_ids = [adm.patient_id for adm in 
            Admission.query.filter_by(status=AdmissionStatus.active).all()]
        
        available_patients = Patient.query.filter(
            ~Patient.id.in_(active_patient_ids)
        ).order_by(Patient.full_name).all()
        
        self.patient_id.choices = [(0, 'اختر المريض')] + [
            (p.id, f'{p.full_name} - {p.file_number}')
            for p in available_patients
        ]
        
        # Get available beds only
        available_beds = Bed.query.filter_by(status=BedStatus.available).order_by(
            Bed.room_number, Bed.bed_label
        ).all()
        
        self.bed_id.choices = [(0, 'اختر السرير')] + [
            (b.id, f'غرفة {b.room_number} - سرير {b.bed_label}')
            for b in available_beds
        ]


class DischargePatientForm(FlaskForm):
    admission_id = HiddenField(validators=[DataRequired()])
    
    discharge_date = DateTimeLocalField(
        'تاريخ ووقت الخروج',
        format='%Y-%m-%dT%H:%M',
        default=datetime.now,
        validators=[DataRequired(message='التاريخ والوقت مطلوبان')]
    )
    
    notes = TextAreaField(
        'ملاحظات الخروج',
        validators=[Optional()],
        render_kw={'rows': 4, 'placeholder': 'حالة المريض عند الخروج، التعليمات...'}
    )
    
    submit = SubmitField('تسجيل الخروج')


class BedStatusForm(FlaskForm):
    status = SelectField(
        'حالة السرير',
        choices=[
            ('available', 'متاح'),
            ('maintenance', 'تحت الصيانة')
        ],
        validators=[DataRequired()]
    )
    
    submit = SubmitField('تحديث الحالة')