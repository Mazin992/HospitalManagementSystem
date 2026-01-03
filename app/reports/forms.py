# app/reports/forms.py - Enhanced date filter form

from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SubmitField
from wtforms.validators import Optional, DataRequired
from datetime import datetime, timedelta


class DateRangeFilterForm(FlaskForm):
    """Enhanced form for filtering reports by date range"""

    preset_range = SelectField(
        'فترة محددة',
        choices=[
            ('today', 'اليوم'),
            ('yesterday', 'أمس'),
            ('this_week', 'هذا الأسبوع'),
            ('last_week', 'الأسبوع الماضي'),
            ('this_month', 'هذا الشهر'),
            ('last_month', 'الشهر الماضي'),
            ('this_quarter', 'هذا الربع'),
            ('this_year', 'هذا العام'),
            ('last_year', 'العام الماضي'),
            ('custom', 'فترة مخصصة')
        ],
        default='this_month'
    )

    start_date = DateField(
        'من تاريخ',
        validators=[DataRequired()],
        format='%Y-%m-%d',
        render_kw={"placeholder": "YYYY-MM-DD"}
    )

    end_date = DateField(
        'إلى تاريخ',
        validators=[DataRequired()],
        format='%Y-%m-%d',
        render_kw={"placeholder": "YYYY-MM-DD"}
    )

    submit = SubmitField('تطبيق الفلتر')

    def __init__(self, *args, **kwargs):
        super(DateRangeFilterForm, self).__init__(*args, **kwargs)

        # Set default dates if not provided (current month)
        if not self.start_date.data:
            now = datetime.now()
            self.start_date.data = datetime(now.year, now.month, 1).date()
        if not self.end_date.data:
            self.end_date.data = datetime.now().date()