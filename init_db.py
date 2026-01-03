import seed_all_permissions
from app import create_app, db
from app.models import Role, User, Service, Bed
from datetime import datetime
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Create all tables using SQLAlchemy
    print('Creating tables via SQLAlchemy...')
    db.create_all()

    # ========================================================================
    # ENSURE ALL TABLES EXIST (Explicit SQL for reliability)
    # ========================================================================

    # 1. Roles table
    print('Creating roles table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            description VARCHAR(255),
            is_system_role BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # 2. Permissions table
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
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_permissions_slug ON permissions(slug)"))

    # 3. Roles-Permissions junction table
    print('Creating roles_permissions junction table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS roles_permissions (
            role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
            permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (role_id, permission_id)
        )
    """))

    # 4. Users table
    print('Creating users table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name_ar VARCHAR(200) NOT NULL,
            role_id INTEGER REFERENCES roles(id) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"))

    # 5. Patients table
    print('Creating patients table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS patients (
            id SERIAL PRIMARY KEY,
            file_number VARCHAR(20) UNIQUE NOT NULL,
            full_name VARCHAR(200) NOT NULL,
            phone VARCHAR(20),
            gender VARCHAR(1),
            dob DATE,
            address TEXT,
            emergency_contact VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_file_number ON patients(file_number)"))

    # 6. Appointments table
    print('Creating appointments table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER REFERENCES patients(id) NOT NULL,
            doctor_id INTEGER REFERENCES users(id) NOT NULL,
            date_time TIMESTAMP NOT NULL,
            status VARCHAR(20) DEFAULT 'pending' NOT NULL,
            type VARCHAR(20) DEFAULT 'scheduled',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_appointments_date_time ON appointments(date_time)"))

    # 7. Medical Visits table
    print('Creating medical_visits table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS medical_visits (
            id SERIAL PRIMARY KEY,
            appointment_id INTEGER REFERENCES appointments(id) UNIQUE NOT NULL,
            doctor_id INTEGER REFERENCES users(id) NOT NULL,
            symptoms TEXT,
            diagnosis TEXT,
            prescription_text TEXT,
            vitals JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # 8. Beds table
    print('Creating beds table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS beds (
            id SERIAL PRIMARY KEY,
            room_number VARCHAR(10) NOT NULL,
            bed_label VARCHAR(10) NOT NULL,
            status VARCHAR(20) DEFAULT 'available' NOT NULL,
            CONSTRAINT uq_room_bed UNIQUE (room_number, bed_label)
        )
    """))

    # 9. Admissions table
    print('Creating admissions table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS admissions (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER REFERENCES patients(id) NOT NULL,
            bed_id INTEGER REFERENCES beds(id) NOT NULL,
            admission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            discharge_date TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active' NOT NULL,
            notes TEXT
        )
    """))

    # 10. Services table
    print('Creating services table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS services (
            id SERIAL PRIMARY KEY,
            name_ar VARCHAR(200) NOT NULL,
            cost_sdg NUMERIC(10, 2) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )
    """))

    # 11. Invoices table
    print('Creating invoices table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER REFERENCES patients(id) NOT NULL,
            total_amount NUMERIC(10, 2) NOT NULL,
            status VARCHAR(20) DEFAULT 'unpaid' NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP
        )
    """))

    # 12. Invoice Items table
    print('Creating invoice_items table...')
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id SERIAL PRIMARY KEY,
            invoice_id INTEGER REFERENCES invoices(id) NOT NULL,
            service_name VARCHAR(200) NOT NULL,
            cost NUMERIC(10, 2) NOT NULL,
            quantity INTEGER DEFAULT 1
        )
    """))

    # Commit structure changes
    db.session.commit()
    print('✓ All tables created successfully')

    # ========================================================================
    # SEED DATA
    # ========================================================================

    # Seed Roles
    print('\nSeeding roles...')
    roles_data = {
        'المشرف العام': {
            'description': 'صلاحيات كاملة على النظام',
            'is_system_role': True
        },
        'طبيب': {
            'description': 'طاقم طبي لديه صلاحيات رعاية المرضى',
            'is_system_role': False
        },
        'ممرض': {
            'description': 'طاقم التمريض بصلاحيات إدارة شؤون المرضى',
            'is_system_role': False
        },
        'الاستقبال': {
            'description': 'استقبال المرضى وتسجيل بياناتهم',
            'is_system_role': False
        },
        'الفوترة': {
            'description': 'إدارة العمليات المالية وإجراءات الفوترة',
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
            role.description = role_attrs['description']
            role.is_system_role = role_attrs['is_system_role']
            print(f'✓ Updated role: {role_name}')

    db.session.commit()

    # Create Admin User
    print('\nCreating admin user...')
    admin_role = Role.query.filter_by(name='المشرف العام').first()
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
        admin_user.role_id = admin_role.id
        print('✓ Updated admin user role')

    # Seed Services
    print('\nAdding services...')
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
    print('\nAdding beds...')
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
    print(f'- Created all required tables')
    print(f'- Created/updated {len(roles_data)} roles')
    print(f'- Created/updated admin user')
    print(f'- Added {len(services_data)} services')
    print(f'- Added {beds_created} beds')
    print(f'- Database schema ready with permission system')

    seed_all_permissions.main()