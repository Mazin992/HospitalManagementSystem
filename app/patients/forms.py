from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Regexp

class PatientForm(FlaskForm):
    full_name = StringField(
        'اسم المريض الكامل',
        validators=[
            DataRequired(message='اسم المريض مطلوب'),
            Length(min=3, max=200, message='الاسم يجب أن يكون بين 3 و 200 حرف')
        ]
    )
    
    phone = StringField(
        'رقم الهاتف',
        validators=[
            DataRequired(message='رقم الهاتف مطلوب'),
            Regexp(r'^[0-9+\-\s()]+$', message='رقم هاتف غير صالح')
        ]
    )
    
    gender = SelectField(
        'الجنس',
        choices=[('', 'اختر الجنس'), ('M', 'ذكر'), ('F', 'أنثى')],
        validators=[Optional()]
    )
    
    dob = DateField(
        'تاريخ الميلاد',
        validators=[Optional()],
        format='%Y-%m-%d'
    )
    
    address = TextAreaField(
        'العنوان',
        validators=[Optional(), Length(max=500)]
    )
    
    emergency_contact = StringField(
        'جهة الاتصال في حالات الطوارئ',
        validators=[Optional(), Length(max=200)]
    )
    
    submit = SubmitField('حفظ')


class PatientSearchForm(FlaskForm):
    search_query = StringField(
        'بحث',
        validators=[Optional()],
        render_kw={'placeholder': 'ابحث بالاسم، رقم الهاتف، أو رقم الملف...'}
    )
    
    search = SubmitField('بحث')