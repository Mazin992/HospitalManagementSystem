from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, FieldList, FormField, \
    HiddenField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Optional, Length
from app.models import Patient, Service, InvoiceStatus

class ServiceForm(FlaskForm):
    name_ar = StringField(
        'اسم الخدمة',
        validators=[
            DataRequired(message='اسم الخدمة مطلوب'),
            Length(min=2, max=200, message='الاسم يجب أن يكون بين 2 و 200 حرف')
        ],
        render_kw={'placeholder': 'مثال: كشف عام، تحليل دم...'}
    )
    
    cost_sdg = DecimalField(
        'السعر (جنيه سوداني)',
        validators=[
            DataRequired(message='السعر مطلوب'),
            NumberRange(min=0, message='السعر يجب أن يكون أكبر من صفر')
        ],
        render_kw={'placeholder': '100.00', 'step': '0.01'}
    )
    
    is_active = BooleanField('نشط', default=True)
    
    submit = SubmitField('حفظ')


class InvoiceItemForm(FlaskForm):
    service_id = SelectField(
        'الخدمة',
        coerce=int,
        validators=[DataRequired(message='يرجى اختيار الخدمة')]
    )
    
    quantity = IntegerField(
        'الكمية',
        default=1,
        validators=[
            DataRequired(message='الكمية مطلوبة'),
            NumberRange(min=1, max=100, message='الكمية يجب أن تكون بين 1 و 100')
        ]
    )
    
    class Meta:
        csrf = False


class CreateInvoiceForm(FlaskForm):
    patient_id = SelectField(
        'المريض',
        coerce=int,
        validators=[DataRequired(message='يرجى اختيار المريض')]
    )
    
    # Dynamic service items will be added via JavaScript
    services = FieldList(FormField(InvoiceItemForm), min_entries=1)
    
    notes = StringField(
        'ملاحظات',
        validators=[Optional(), Length(max=500)]
    )
    
    submit = SubmitField('إنشاء الفاتورة')
    
    def __init__(self, *args, **kwargs):
        super(CreateInvoiceForm, self).__init__(*args, **kwargs)
        
        # Populate patient choices
        patients = Patient.query.order_by(Patient.full_name).all()
        self.patient_id.choices = [(0, 'اختر المريض')] + [
            (p.id, f'{p.full_name} - {p.file_number}')
            for p in patients
        ]
        
        # Populate service choices for all item forms
        services = Service.query.filter_by(is_active=True).order_by(Service.name_ar).all()
        service_choices = [(0, 'اختر الخدمة')] + [
            (s.id, f'{s.name_ar} - {float(s.cost_sdg)} ج.س')
            for s in services
        ]
        
        for item_form in self.services:
            item_form.service_id.choices = service_choices


class PaymentForm(FlaskForm):
    payment_method = SelectField(
        'طريقة الدفع',
        choices=[
            ('cash', 'نقداً'),
            ('card', 'بطاقة'),
            ('insurance', 'تأمين'),
            ('bank_transfer', 'حوالة بنكية')
        ],
        validators=[DataRequired()]
    )
    
    amount_paid = DecimalField(
        'المبلغ المدفوع (ج.س)',
        validators=[
            DataRequired(message='المبلغ المدفوع مطلوب'),
            NumberRange(min=0, message='المبلغ يجب أن يكون أكبر من صفر')
        ],
        render_kw={'step': '0.01'}
    )
    
    reference_number = StringField(
        'رقم المرجع (اختياري)',
        validators=[Optional(), Length(max=100)],
        render_kw={'placeholder': 'رقم الشيك، رقم العملية...'}
    )
    
    notes = StringField(
        'ملاحظات',
        validators=[Optional(), Length(max=500)]
    )
    
    submit = SubmitField('تسجيل الدفع')