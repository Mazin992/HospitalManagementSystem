from app import create_app, db
from app.models import Role, User, Service, Bed
from datetime import datetime
from sqlalchemy import text  # Add this import

app = create_app()

with app.app_context():
    # Create all tables
    print('Creating tables...')
    db.create_all()

    # 1. Create permissions table if not exists
    print('Creating permissions table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS permissions (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            description VARCHAR(255),
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # Create index for permissions
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_permissions_slug ON permissions(slug)"))

    # 2. Create roles_permissions junction table
    print('Creating roles_permissions junction table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS roles_permissions (
            role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
            permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (role_id, permission_id)
        )
    """))

    # 3. Add new columns to roles table
    print('Altering roles table...')

    # Check if columns exist before adding
    try:
        db.session.execute(text("ALTER TABLE roles ADD COLUMN IF NOT EXISTS description VARCHAR(255)"))
    except:
        pass  # Column might already exist

    try:
        db.session.execute(text("ALTER TABLE roles ADD COLUMN IF NOT EXISTS is_system_role BOOLEAN DEFAULT FALSE"))
    except:
        pass

    try:
        db.session.execute(text("ALTER TABLE roles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    except:
        pass

    # 4. Add new column to users table
    print('Altering users table...')
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP"))
    except:
        pass

    # Commit structure changes first
    db.session.commit()

    # Seed Roles (now using new permission system)
    print('Creating roles...')
    roles_data = {
        'Super Admin': {
            'description': 'Full system access',
            'is_system_role': True
        },
        'Doctor': {
            'description': 'Medical staff with patient care privileges',
            'is_system_role': False
        },
        'Nurse': {
            'description': 'Nursing staff with patient management access',
            'is_system_role': False
        },
        'Reception': {
            'description': 'Front desk and patient registration',
            'is_system_role': False
        },
        'Billing': {
            'description': 'Financial and billing operations',
            'is_system_role': False
        }
    }

    for role_name, role_attrs in roles_data.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(
                name=role_name,
                description=role_attrs['description'],
                is_system_role=role_attrs['is_system_role']
            )
            db.session.add(role)
            print(f'✓ Created role: {role_name}')
        else:
            # Update existing role with new fields
            role.description = role_attrs['description']
            role.is_system_role = role_attrs['is_system_role']
            print(f'✓ Updated role: {role_name}')

    db.session.commit()

    # 5. Remove old JSON permissions column from roles (if it exists)
    print('Removing old permissions column...')
    try:
        # First, check if the column exists
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='roles' AND column_name='permissions'
        """)).fetchone()

        if result:
            db.session.execute(text("ALTER TABLE roles DROP COLUMN permissions"))
            print('✓ Removed old permissions column')
    except Exception as e:
        print(f'Note: Could not drop permissions column: {e}')

    # Create Admin User
    print('Creating admin user...')
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
        print('✓ Created admin user (username: admin, password: admin)')
    else:
        # Ensure admin user has the correct role
        admin_user.role_id = admin_role.id
        print('✓ Updated admin user role')

    # Seed Services
    print('Adding services...')
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
    ]

    for name_ar, cost in services_data:
        service = Service.query.filter_by(name_ar=name_ar).first()
        if not service:
            service = Service(name_ar=name_ar, cost_sdg=cost)
            db.session.add(service)
            print(f'✓ Added service: {name_ar}')

    # Seed Beds
    print('Adding beds...')
    rooms = ['101', '102', '103', '201', '202', '203']
    beds_per_room = ['A', 'B']

    beds_created = 0
    for room in rooms:
        for bed_label in beds_per_room:
            bed = Bed.query.filter_by(room_number=room, bed_label=bed_label).first()
            if not bed:
                bed = Bed(room_number=room, bed_label=bed_label, status='available')
                db.session.add(bed)
                beds_created += 1

    print(f'✓ Added {beds_created} beds')

    # Final commit
    db.session.commit()

    print('\n' + '=' * 50)
    print('✅ Database initialized successfully!')
    print('=' * 50)
    print('🔐 Login credentials: admin / admin')
    print('⚠️  IMPORTANT: Change the admin password after first login!')
    print('\nSummary:')
    print(f'- Created/updated {len(roles_data)} roles')
    print(f'- Created/updated admin user')
    print(f'- Added {len(services_data)} services')
    print(f'- Added {beds_created} beds')
    print(f'- Updated database schema with new permission system')