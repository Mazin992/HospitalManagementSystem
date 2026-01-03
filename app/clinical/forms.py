from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

class MedicalVisitForm(FlaskForm):
    symptoms = TextAreaField(
        'الأعراض',
        validators=[DataRequired(message='يرجى إدخال الأعراض')],
        render_kw={'rows': 4, 'placeholder': 'اكتب الأعراض التي يشكو منها المريض...'}
    )
    
    diagnosis = TextAreaField(
        'التشخيص',
        validators=[DataRequired(message='التشخيص مطلوب')],
        render_kw={'rows': 4, 'placeholder': 'اكتب التشخيص الطبي...'}
    )
    
    prescription_text = TextAreaField(
        'الوصفة الطبية',
        validators=[Optional()],
        render_kw={'rows': 5, 'placeholder': 'اكتب الأدوية والجرعات...\nمثال:\n- دواء أ: قرص واحد صباحاً ومساءً\n- دواء ب: ملعقة كبيرة 3 مرات يومياً'}
    )
    
    # Vitals (Optional)
    temperature = DecimalField(
        'درجة الحرارة (°C)',
        validators=[Optional(), NumberRange(min=30, max=45, message='درجة حرارة غير صحيحة')],
        render_kw={'placeholder': '37.0', 'step': '0.1'}
    )
    
    blood_pressure = StringField(
        'ضغط الدم',
        validators=[Optional()],
        render_kw={'placeholder': '120/80'}
    )
    
    heart_rate = DecimalField(
        'نبضات القلب (bpm)',
        validators=[Optional(), NumberRange(min=40, max=200, message='معدل نبض غير صحيح')],
        render_kw={'placeholder': '75'}
    )
    
    weight = DecimalField(
        'الوزن (kg)',
        validators=[Optional(), NumberRange(min=0.5, max=300, message='وزن غير صحيح')],
        render_kw={'placeholder': '70.5', 'step': '0.1'}
    )
    
    height = DecimalField(
        'الطول (cm)',
        validators=[Optional(), NumberRange(min=30, max=250, message='طول غير صحيح')],
        render_kw={'placeholder': '170'}
    )
    
    notes = TextAreaField(
        'ملاحظات إضافية',
        validators=[Optional()],
        render_kw={'rows': 3, 'placeholder': 'أي ملاحظات أو تعليمات إضافية...'}
    )
    
    submit = SubmitField('حفظ وإنهاء الكشف')