# app/admin/routes.py

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.admin import bp
from app.admin.forms import UserForm, ChangePasswordForm, RoleForm
from app.models import User, Role, Permission
from app import db
from functools import wraps

def admin_required(f):
    """Decorator to require admin permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يرجى تسجيل الدخول أولاً.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check if user has admin access permission
        if not current_user.can('users.view'):
            flash('ليس لديك صلاحية للوصول إلى لوحة الإدارة.', 'danger')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard overview"""
    # Statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_roles = Role.query.count()
    total_permissions = Permission.query.count()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Users by role
    roles_with_counts = db.session.query(
        Role.name, 
        db.func.count(User.id)
    ).join(User).group_by(Role.name).all()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        active_users=active_users,
        total_roles=total_roles,
        total_permissions=total_permissions,
        recent_users=recent_users,
        roles_with_counts=roles_with_counts
    )


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@bp.route('/users')
@login_required
@admin_required
def users_list():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', 0, type=int)
    status_filter = request.args.get('status', 'all')
    
    # Base query
    query = User.query
    
    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.full_name_ar.ilike(f'%{search}%')
            )
        )
    
    # Apply role filter
    if role_filter > 0:
        query = query.filter_by(role_id=role_filter)
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    # Pagination
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get all roles for filter dropdown
    roles = Role.query.order_by(Role.name).all()
    
    return render_template(
        'admin/users.html',
        users=users,
        roles=roles,
        search=search,
        role_filter=role_filter,
        status_filter=status_filter
    )


@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user"""
    if not current_user.can('users.create'):
        flash('ليس لديك صلاحية لإنشاء مستخدمين جدد.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    form = UserForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            full_name_ar=form.full_name_ar.data.strip(),
            role_id=form.role_id.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'تم إنشاء المستخدم "{user.username}" بنجاح.', 'success')
            return redirect(url_for('admin.users_list'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إنشاء المستخدم. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('admin/user_form.html', form=form, title='إنشاء مستخدم جديد')


@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit existing user"""
    if not current_user.can('users.edit'):
        flash('ليس لديك صلاحية لتعديل المستخدمين.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent editing yourself through this route
    if user.id == current_user.id:
        flash('لا يمكنك تعديل حسابك الخاص من هنا. استخدم إعدادات الحساب.', 'warning')
        return redirect(url_for('admin.users_list'))
    
    form = UserForm(user=user, obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data.strip()
        user.full_name_ar = form.full_name_ar.data.strip()
        user.role_id = form.role_id.data
        user.is_active = form.is_active.data
        
        # Update password if provided
        if form.password.data:
            user.set_password(form.password.data)
        
        try:
            db.session.commit()
            flash(f'تم تحديث بيانات المستخدم "{user.username}" بنجاح.', 'success')
            return redirect(url_for('admin.users_list'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء التحديث. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('admin/user_form.html', form=form, title='تعديل المستخدم', user=user)


@bp.route('/users/<int:user_id>/password', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_password(user_id):
    """Change user password"""
    if not current_user.can('users.edit'):
        flash('ليس لديك صلاحية لتغيير كلمات المرور.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    user = User.query.get_or_404(user_id)
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        
        try:
            db.session.commit()
            flash(f'تم تغيير كلمة مرور المستخدم "{user.username}" بنجاح.', 'success')
            return redirect(url_for('admin.users_list'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تغيير كلمة المرور.', 'danger')
    
    return render_template('admin/change_password.html', form=form, user=user)


@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    if not current_user.can('users.edit'):
        flash('ليس لديك صلاحية لتعديل حالة المستخدمين.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent disabling yourself
    if user.id == current_user.id:
        flash('لا يمكنك تعطيل حسابك الخاص!', 'danger')
        return redirect(url_for('admin.users_list'))
    
    user.is_active = not user.is_active
    
    try:
        db.session.commit()
        status = 'تفعيل' if user.is_active else 'تعطيل'
        flash(f'تم {status} حساب المستخدم "{user.username}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ. يرجى المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('admin.users_list'))


@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    if not current_user.can('users.delete'):
        flash('ليس لديك صلاحية لحذف المستخدمين.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص!', 'danger')
        return redirect(url_for('admin.users_list'))
    
    # Check if user has associated records
    if user.appointments_as_doctor.count() > 0:
        flash(f'لا يمكن حذف المستخدم "{user.username}" لأن لديه مواعيد مسجلة.', 'warning')
        return redirect(url_for('admin.users_list'))
    
    username = user.username
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'تم حذف المستخدم "{username}" بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء الحذف. يرجى المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('admin.users_list'))


# ============================================================================
# ROLE MANAGEMENT
# ============================================================================

@bp.route('/roles')
@login_required
@admin_required
def roles_list():
    """List all roles"""
    if not current_user.can('users.manage_roles'):
        flash('ليس لديك صلاحية لإدارة الأدوار.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    roles = Role.query.order_by(Role.name).all()
    
    # Get user count for each role
    role_stats = {}
    for role in roles:
        role_stats[role.id] = {
            'user_count': role.users.count(),
            'permission_count': len(role.permissions)
        }
    
    return render_template('admin/roles.html', roles=roles, role_stats=role_stats)


@bp.route('/roles/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_role():
    """Create new role"""
    if not current_user.can('users.manage_roles'):
        flash('ليس لديك صلاحية لإنشاء أدوار جديدة.', 'danger')
        return redirect(url_for('admin.roles_list'))
    
    form = RoleForm()
    
    # Get permissions grouped by category
    permissions_by_category = {}
    all_permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    for perm in all_permissions:
        if perm.category not in permissions_by_category:
            permissions_by_category[perm.category] = []
        permissions_by_category[perm.category].append(perm)
    
    if form.validate_on_submit():
        role = Role(
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            is_system_role=False
        )
        
        # Add selected permissions
        selected_ids = form.get_selected_permissions()
        role.permissions = Permission.query.filter(Permission.id.in_(selected_ids)).all()
        
        try:
            db.session.add(role)
            db.session.commit()
            return redirect(url_for('admin.roles_list'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إنشاء الدور. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template(
        'admin/role_form.html', 
        form=form, 
        title='إنشاء دور جديد',
        permissions_by_category=permissions_by_category
    )


@bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)

    if role.is_system_role:
        flash('لا يمكن تعديل أدوار النظام الأساسية.', 'warning')
        return redirect(url_for('admin.roles_list'))
    form = RoleForm(obj=role, role=role)

    if form.validate_on_submit():
        role = db.session.merge(role)
        role.name = form.name.data.strip()
        role.description = form.description.data.strip() if form.description.data else None

        selected_ids = form.get_selected_permissions()

        # This line will now work because Permission is imported at the top
        role.permissions = Permission.query.filter(Permission.id.in_(selected_ids)).all()

        try:
            db.session.commit()
            flash(f'تم تحديث الدور "{role.name}" بنجاح.', 'success')
            return redirect(url_for('admin.roles_list'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تحديث الدور.', 'danger')

    # Grouping logic for the template
    all_permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    permissions_by_category = {}
    for perm in all_permissions:
        if perm.category not in permissions_by_category:
            permissions_by_category[perm.category] = []
        permissions_by_category[perm.category].append(perm)

    return render_template(
        'admin/role_form.html',
        title='تعديل دور',
        form=form,
        role=role,
        permissions_by_category=permissions_by_category
    )


@bp.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_role(role_id):
    """Delete role"""
    if not current_user.can('users.manage_roles'):
        flash('ليس لديك صلاحية لحذف الأدوار.', 'danger')
        return redirect(url_for('admin.roles_list'))
    
    role = Role.query.get_or_404(role_id)
    
    # Prevent deleting system roles
    if role.is_system_role:
        flash('لا يمكن حذف أدوار النظام الافتراضية.', 'danger')
        return redirect(url_for('admin.roles_list'))
    
    # Check if role has users
    if role.users.count() > 0:
        flash(f'لا يمكن حذف الدور "{role.name}" لأن هناك {role.users.count()} مستخدم مرتبط به.', 'warning')
        return redirect(url_for('admin.roles_list'))
    
    role_name = role.name
    
    try:
        db.session.delete(role)
        db.session.commit()
        flash(f'تم حذف الدور "{role_name}" بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء الحذف. يرجى المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('admin.roles_list'))


@bp.route('/roles/<int:role_id>')
@login_required
@admin_required
def view_role(role_id):
    """View role details"""
    if not current_user.can('users.manage_roles'):
        flash('ليس لديك صلاحية لعرض تفاصيل الأدوار.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    role = Role.query.get_or_404(role_id)
    
    # Get permissions grouped by category
    permissions_by_category = {}
    for perm in role.permissions:
        if perm.category not in permissions_by_category:
            permissions_by_category[perm.category] = []
        permissions_by_category[perm.category].append(perm)
    
    # Get users with this role
    users = role.users.order_by(User.full_name_ar).all()
    
    return render_template(
        'admin/role_detail.html',
        role=role,
        permissions_by_category=permissions_by_category,
        users=users
    )