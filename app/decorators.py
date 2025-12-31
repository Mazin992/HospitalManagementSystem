from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(*role_names):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يرجى تسجيل الدخول أولاً.', 'warning')  # Please login first
                return redirect(url_for('auth.login'))
            
            if not current_user.is_active:
                flash('حسابك غير نشط. يرجى الاتصال بالمسؤول.', 'danger')  # Account inactive
                return redirect(url_for('auth.login'))
            
            if current_user.role.name not in role_names and 'Super Admin' not in role_names:
                # Allow Super Admin to access everything
                if current_user.role.name != 'Super Admin':
                    flash('ليس لديك صلاحية للوصول إلى هذه الصفحة.', 'danger')  # No permission
                    return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(resource, action):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يرجى تسجيل الدخول أولاً.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.has_permission(resource, action):
                # Super Admin bypasses all permission checks
                if current_user.role.name != 'Super Admin':
                    flash('ليس لديك صلاحية لتنفيذ هذا الإجراء.', 'danger')  # No permission for this action
                    return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator