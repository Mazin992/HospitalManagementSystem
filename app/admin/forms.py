# app/admin/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError, Optional, EqualTo
from app.models import User, Role, Permission
from app import db
from flask import request

class UserForm(FlaskForm):
    """Form for creating and editing users"""
    username = StringField(
        'اسم المستخدم',
        validators=[
            DataRequired(message='اسم المستخدم مطلوب'),
            Length(min=3, max=80, message='اسم المستخدم يجب أن يكون بين 3 و 80 حرف')
        ],
        render_kw={'placeholder': 'أدخل اسم المستخدم'}
    )
    
    full_name_ar = StringField(
        'الاسم الكامل',
        validators=[
            DataRequired(message='الاسم الكامل مطلوب'),
            Length(min=3, max=200, message='الاسم يجب أن يكون بين 3 و 200 حرف')
        ],
        render_kw={'placeholder': 'أدخل الاسم الكامل'}
    )
    
    role_id = SelectField(
        'الدور الوظيفي',
        coerce=int,
        validators=[DataRequired(message='يرجى اختيار الدور')]
    )
    
    is_active = BooleanField('حساب نشط', default=True)
    
    # Password fields (only for new users)
    password = PasswordField(
        'كلمة المرور',
        validators=[Optional(), Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')]
    )
    
    confirm_password = PasswordField(
        'تأكيد كلمة المرور',
        validators=[
            Optional(),
            EqualTo('password', message='كلمات المرور غير متطابقة')
        ]
    )
    
    submit = SubmitField('حفظ')
    
    def __init__(self, user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        
        # Populate role choices
        self.role_id.choices = [(0, 'اختر الدور')] + [
            (r.id, r.name) for r in Role.query.order_by(Role.name).all()
        ]
        
        self.user = user
        
        # If editing existing user, password is optional
        if user:
            self.password.validators = [Optional()]
            self.confirm_password.validators = [Optional()]
        else:
            # For new users, password is required
            self.password.validators = [
                DataRequired(message='كلمة المرور مطلوبة'),
                Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')
            ]
            self.confirm_password.validators = [
                DataRequired(message='تأكيد كلمة المرور مطلوب'),
                EqualTo('password', message='كلمات المرور غير متطابقة')
            ]
    
    def validate_username(self, field):
        """Check if username already exists"""
        existing_user = User.query.filter_by(username=field.data).first()
        if existing_user and (not self.user or existing_user.id != self.user.id):
            raise ValidationError('اسم المستخدم موجود بالفعل. اختر اسماً آخر.')


class ChangePasswordForm(FlaskForm):
    """Form for changing user password"""
    new_password = PasswordField(
        'كلمة المرور الجديدة',
        validators=[
            DataRequired(message='كلمة المرور الجديدة مطلوبة'),
            Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')
        ]
    )
    
    confirm_password = PasswordField(
        'تأكيد كلمة المرور',
        validators=[
            DataRequired(message='تأكيد كلمة المرور مطلوب'),
            EqualTo('new_password', message='كلمات المرور غير متطابقة')
        ]
    )
    
    submit = SubmitField('تغيير كلمة المرور')


class RoleForm(FlaskForm):
    """Form for creating and editing roles with permissions"""
    name = StringField(
        'اسم الدور',
        validators=[
            DataRequired(message='اسم الدور مطلوب'),
            Length(min=2, max=50, message='الاسم يجب أن يكون بين 2 و 50 حرف')
        ],
        render_kw={'placeholder': 'مثال: موظف استقبال'}
    )

    description = TextAreaField(
        'الوصف',
        validators=[Optional(), Length(max=255)],
        render_kw={'rows': 3, 'placeholder': 'وصف مختصر لمهام هذا الدور...'}
    )

    submit = SubmitField('حفظ الدور')

    def __init__(self, role=None, *args, **kwargs):
        # 1. Initialize the base form first
        super(RoleForm, self).__init__(*args, **kwargs)
        self.role = role

        # 2. Add dynamic fields
        try:
            # Import here to avoid circular dependencies
            from app.models import Permission
            permissions = Permission.query.order_by(Permission.category, Permission.name).all()

            for perm in permissions:
                field_name = f'perm_{perm.id}'
                # Create a BooleanField instance
                field = BooleanField(perm.name)

                # Bind the field to this form instance
                bound_field = field.bind(form=self, name=field_name)
                self._fields[field_name] = bound_field

                # --- FIX STARTS HERE ---
                # 3. Manually process the field
                if self.is_submitted():
                    # If form is submitted (POST), process data from request.form
                    bound_field.process(formdata=request.form)
                elif role:
                    # If editing (GET) and role exists, check DB for existing permissions
                    if any(p.id == perm.id for p in role.permissions):
                        bound_field.data = True
                    else:
                        bound_field.data = False
                else:
                    # If creating new (GET), initialize as False
                    bound_field.data = False
                # --- FIX ENDS HERE ---

        except Exception as e:
            print(f"Error in RoleForm init: {e}")

    def get_selected_permissions(self):
        """Helper to get list of permission IDs that were checked"""
        permission_ids = []
        for field_name, field in self._fields.items():
            if field_name.startswith('perm_') and field.data:
                try:
                    perm_id = int(field_name.split('_')[1])
                    permission_ids.append(perm_id)
                except (ValueError, IndexError):
                    continue
        return permission_ids
    
    def validate_name(self, field):
        """Check if role name already exists"""
        existing_role = Role.query.filter_by(name=field.data).first()
        if existing_role and (not self.role or existing_role.id != self.role.id):
            raise ValidationError('اسم الدور موجود بالفعل. اختر اسماً آخر.')
