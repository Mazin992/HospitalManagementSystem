from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import bp
from app.auth.forms import LoginForm
from app import db
from app.models import User
from app.admin.forms import ChangePasswordForm

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'danger')  # Invalid credentials
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('حسابك غير نشط. يرجى الاتصال بالمسؤول.', 'warning')  # Account inactive
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        flash(f'مرحباً {user.full_name_ar}!', 'success')  # Welcome!
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.dashboard')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = current_user
        user.set_password(form.new_password.data)
        db.session.commit()
        flash('تم تغيير كلمة المرور بنجاح.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/change_password.html', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح.', 'info')  # Logged out successfully
    return redirect(url_for('auth.login'))
