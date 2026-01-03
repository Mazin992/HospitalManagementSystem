from flask_wtf import FlaskForm
from wtforms import SelectField, DateTimeLocalField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional
from app.models import Patient, User
from app import db

class AppointmentForm(FlaskForm):
    patient_id = SelectField(
        'المريض',
        coerce=int,
        validators=[DataRequired(message='يرجى اختيار المريض')]
    )
    
    doctor_id = SelectField(
        'الطبيب',
        coerce=int,
        validators=[DataRequired(message='يرجى اختيار الطبيب')]
    )
    
    date_time = DateTimeLocalField(
        'التاريخ والوقت',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message='التاريخ والوقت مطلوبان')]
    )
    
    type = SelectField(
        'نوع الموعد',
        choices=[
            ('scheduled', 'موعد محجوز'),
            ('walk-in', 'مراجعة طارئة')
        ],
        validators=[DataRequired()]
    )
    
    notes = TextAreaField(
        'ملاحظات',
        validators=[Optional()]
    )
    
    submit = SubmitField('حجز الموعد')
    
    def __init__(self, *args, **kwargs):
        super(AppointmentForm, self).__init__(*args, **kwargs)
        
        # Populate patient choices
        self.patient_id.choices = [(0, 'اختر المريض')] + [
            (p.id, f'{p.full_name} - {p.file_number}')
            for p in Patient.query.order_by(Patient.full_name).all()
        ]
        
        # Populate doctor choices (users with Doctor role)
        doctors = User.query.join(User.role).filter(
            db.or_(
                db.func.lower(db.text("roles.name")) == 'doctor',
                db.func.lower(db.text("roles.name")) == 'super admin'
            )
        ).filter(User.is_active == True).all()
        
        self.doctor_id.choices = [(0, 'اختر الطبيب')] + [
            (d.id, d.full_name_ar) for d in doctors
        ]


class QuickAppointmentForm(FlaskForm):
    """Quick form when patient is already selected"""
    patient_id = HiddenField(validators=[DataRequired()])
    
    doctor_id = SelectField(
        'الطبيب',
        coerce=int,
        validators=[DataRequired(message='يرجى اختيار الطبيب')]
    )
    
    date_time = DateTimeLocalField(
        'التاريخ والوقت',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message='التاريخ والوقت مطلوبان')]
    )
    
    type = SelectField(
        'نوع الموعد',
        choices=[
            ('scheduled', 'موعد محجوز'),
            ('walk-in', 'مراجعة طارئة')
        ],
        validators=[DataRequired()]
    )
    
    notes = TextAreaField('ملاحظات', validators=[Optional()])
    submit = SubmitField('حجز الموعد')