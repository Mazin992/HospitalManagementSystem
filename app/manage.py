# app/manage.py - Updated with permission seeding

from app import create_app, db
from app.models import Role, User, Service, Bed, Permission
import click

app = create_app()


@app.cli.command()
def seed_permissions():
    '''Seed granular permissions and migrate existing roles'''
    click.echo('🔐 Seeding permissions...')

    # Define all granular permissions
    permissions_data = [
        # Patient Management
        ('patients.view', 'View Patients', 'View patient list and details', 'patients'),
        ('patients.create', 'Create Patient', 'Register new patients', 'patients'),
        ('patients.edit', 'Edit Patient', 'Update patient information', 'patients'),
        ('patients.delete', 'Delete Patient', 'Remove patients from system', 'patients'),

        # Appointments
        ('appointments.view', 'View Appointments', 'View appointment list and details', 'appointments'),
        ('appointments.create', 'Create Appointment', 'Book new appointments', 'appointments'),
        ('appointments.edit', 'Edit Appointment', 'Modify appointment details', 'appointments'),
        ('appointments.cancel', 'Cancel Appointment', 'Cancel appointments', 'appointments'),
        ('appointments.view_own', 'View Own Appointments', 'View only assigned appointments', 'appointments'),

        # Clinical/Medical Records
        ('clinical.view', 'View Medical Records', 'View patient medical history', 'clinical'),
        ('clinical.create', 'Create Medical Record', 'Document consultations', 'clinical'),
        ('clinical.edit', 'Edit Medical Record', 'Update medical records', 'clinical'),
        ('clinical.view_own', 'View Own Records', 'View only own consultations', 'clinical'),

        # Facility/Beds
        ('facility.view', 'View Beds', 'View bed status and admissions', 'facility'),
        ('facility.admit', 'Admit Patient', 'Admit patients to beds', 'facility'),
        ('facility.discharge', 'Discharge Patient', 'Discharge patients', 'facility'),
        ('facility.manage_beds', 'Manage Beds', 'Change bed status', 'facility'),

        # Billing
        ('billing.view', 'View Invoices', 'View billing and invoices', 'billing'),
        ('billing.create', 'Create Invoice', 'Generate new invoices', 'billing'),
        ('billing.process_payment', 'Process Payment', 'Record payments', 'billing'),
        ('billing.manage_services', 'Manage Services', 'Add/edit medical services', 'billing'),

        # User Management
        ('users.view', 'View Users', 'View user list', 'users'),
        ('users.create', 'Create User', 'Add new system users', 'users'),
        ('users.edit', 'Edit User', 'Modify user details', 'users'),
        ('users.delete', 'Delete User', 'Remove users', 'users'),
        ('users.manage_roles', 'Manage Roles', 'Assign roles and permissions', 'users'),

        # Reports
        ('reports.view', 'View Reports', 'Access system reports', 'reports'),
        ('reports.export', 'Export Reports', 'Export data', 'reports'),
    ]

    # Create permissions
    created_permissions = {}
    for slug, name, description, category in permissions_data:
        perm = Permission.query.filter_by(slug=slug).first()
        if not perm:
            perm = Permission(slug=slug, name=name, description=description, category=category)
            db.session.add(perm)
            click.echo(f'✓ Created permission: {slug}')
        created_permissions[slug] = perm

    db.session.commit()

    # Define role-permission mappings (migrating from old system)
    role_permissions = {
        'Super Admin': [
            'patients.view', 'patients.create', 'patients.edit', 'patients.delete',
            'appointments.view', 'appointments.create', 'appointments.edit', 'appointments.cancel',
            'clinical.view', 'clinical.create', 'clinical.edit',
            'facility.view', 'facility.admit', 'facility.discharge', 'facility.manage_beds',
            'billing.view', 'billing.create', 'billing.process_payment', 'billing.manage_services',
            'users.view', 'users.create', 'users.edit', 'users.delete', 'users.manage_roles',
            'reports.view', 'reports.export'
        ],
        'Doctor': [
            'patients.view',
            'appointments.view_own', 'appointments.create', 'appointments.edit',
            'clinical.view', 'clinical.create', 'clinical.edit', 'clinical.view_own',
            'facility.view'
        ],
        'Nurse': [
            'patients.view',
            'appointments.view',
            'clinical.view',
            'facility.view', 'facility.admit', 'facility.discharge', 'facility.manage_beds'
        ],
        'Reception': [
            'patients.view', 'patients.create', 'patients.edit', 'patients.delete',
            'appointments.view', 'appointments.create', 'appointments.edit', 'appointments.cancel',
            'billing.view', 'billing.create'
        ],
        'Billing': [
            'patients.view',
            'billing.view', 'billing.create', 'billing.process_payment', 'billing.manage_services',
            'reports.view', 'reports.export'
        ]
    }

    # Assign permissions to roles
    for role_name, permission_slugs in role_permissions.items():
        role = Role.query.filter_by(name=role_name).first()
        if role:
            # Clear existing permissions
            role.permissions = []

            # Assign new permissions
            for slug in permission_slugs:
                if slug in created_permissions:
                    role.grant_permission(created_permissions[slug])

            role.is_system_role = True  # Mark as system role
            click.echo(f'✓ Updated {role_name} with {len(permission_slugs)} permissions')

    db.session.commit()
    click.echo('\n✅ Permission seeding completed!')


@app.cli.command()
def seed_db():
    '''Seed database with default roles, admin user, services, and beds'''
    click.echo('🌱 Starting database seeding...')

    # Create all tables
    db.create_all()
    click.echo('✓ Tables created')

    # SEED ROLES (basic structure only)
    roles_data = {
        'Super Admin': 'Full system access',
        'Doctor': 'Medical consultations and records',
        'Nurse': 'Patient care and admissions',
        'Reception': 'Patient registration and scheduling',
        'Billing': 'Financial and billing operations'
    }

    for role_name, description in roles_data.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=description, is_system_role=True)
            db.session.add(role)
            click.echo(f'✓ Created role: {role_name}')

    db.session.commit()

    # SEED ADMIN USER
    admin_role = Role.query.filter_by(name='Super Admin').first()
    admin_user = User.query.filter_by(username='admin').first()

    if not admin_user:
        admin_user = User(
            username='admin',
            full_name_ar='المسؤول الرئيسي',
            role_id=admin_role.id,
            is_active=True
        )
        admin_user.set_password('admin')
        db.session.add(admin_user)
        click.echo('✓ Created admin user (username: admin, password: admin)')

    # SEED SERVICES
    services_data = [
        ('كشف عام', 100.00),
        ('كشف متخصص', 200.00),
        ('تحليل دم شامل', 150.00),
        ('أشعة سينية', 250.00),
        ('أشعة مقطعية', 500.00),
        ('تحليل بول', 50.00),
        ('إقامة يومية', 300.00),
        ('عملية صغرى', 1000.00),
        ('عملية كبرى', 5000.00),
        ('كشف أسنان', 120.00),
        ('تنظيف أسنان', 150.00),
        ('خلع ضرس', 200.00),
    ]

    for name_ar, cost in services_data:
        service = Service.query.filter_by(name_ar=name_ar).first()
        if not service:
            service = Service(name_ar=name_ar, cost_sdg=cost)
            db.session.add(service)
            click.echo(f'✓ Created service: {name_ar}')

    # SEED BEDS
    rooms = ['101', '102', '103', '201', '202', '203']
    beds_per_room = ['A', 'B']

    for room in rooms:
        for bed_label in beds_per_room:
            bed = Bed.query.filter_by(room_number=room, bed_label=bed_label).first()
            if not bed:
                bed = Bed(room_number=room, bed_label=bed_label, status='available')
                db.session.add(bed)
                click.echo(f'✓ Created bed: {room}-{bed_label}')

    db.session.commit()
    click.echo('\n✅ Database seeding completed!')
    click.echo('🔒 Login credentials: admin / admin')
    click.echo('⚠️  Run "flask seed-permissions" to set up granular permissions')


@app.cli.command()
def init_db():
    '''Initialize the database (drop and recreate all tables)'''
    click.echo('⚠️  This will DROP all existing tables!')
    if click.confirm('Are you sure?'):
        db.drop_all()
        db.create_all()
        click.echo('✓ Database initialized')
        click.echo('Run "flask seed-db" to populate with initial data')


@app.cli.command()
@click.argument('username')
@click.argument('password')
@click.argument('full_name')
@click.argument('role_name')
def create_user(username, password, full_name, role_name):
    '''Create a new user'''
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        click.echo(f'✖ Role "{role_name}" not found')
        click.echo('Available roles: Super Admin, Doctor, Nurse, Reception, Billing')
        return

    existing = User.query.filter_by(username=username).first()
    if existing:
        click.echo(f'✖ User "{username}" already exists')
        return

    user = User(
        username=username,
        full_name_ar=full_name,
        role_id=role.id,
        is_active=True
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    click.echo(f'✅ User "{username}" created successfully')
    click.echo(f'Role: {role_name}')


@app.cli.command()
def test_stats():
    '''Test the statistics service'''
    from app.services.stats_service import StatsService
    import json

    click.echo('📊 Testing Statistics Service...\n')

    # Get all dashboard stats
    stats = StatsService.get_dashboard_stats()

    # Display formatted output
    click.echo('=' * 60)
    click.echo('REVENUE')
    click.echo('=' * 60)
    click.echo(f"Today: {stats['revenue']['today']:.2f} SDG")
    click.echo(f"This Month: {stats['revenue']['this_month']:.2f} SDG")
    click.echo(f"This Year: {stats['revenue']['this_year']:.2f} SDG")
    click.echo(f"Monthly Growth: {stats['revenue']['growth']['monthly']}%\n")

    click.echo('=' * 60)
    click.echo('PATIENTS')
    click.echo('=' * 60)
    click.echo(f"Total: {stats['patients']['total']}")
    click.echo(f"New Today: {stats['patients']['new_today']}")
    click.echo(f"New This Month: {stats['patients']['new_this_month']}\n")

    click.echo('=' * 60)
    click.echo('APPOINTMENTS')
    click.echo('=' * 60)
    click.echo(f"Total This Month: {stats['appointments']['total']}")
    click.echo(f"Completed: {stats['appointments']['by_status']['completed']}")
    click.echo(f"Completion Rate: {stats['appointments']['completion_rate']}%\n")

    click.echo('=' * 60)
    click.echo('BED OCCUPANCY')
    click.echo('=' * 60)
    click.echo(f"Occupancy Rate: {stats['bed_occupancy']['occupancy_rate']}%")
    click.echo(f"Available: {stats['bed_occupancy']['available']}/{stats['bed_occupancy']['total_beds']}\n")

    click.echo('✅ Statistics service is working correctly!')


if __name__ == '__main__':
    app.run(debug=True)