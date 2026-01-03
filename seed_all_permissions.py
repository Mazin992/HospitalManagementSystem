#!/usr/bin/env python
"""
Comprehensive Permission Seeding Script
Seeds ALL permissions for the Hospital Management System and assigns them to roles.

Usage:
    python seed_all_permissions.py
"""

from app import create_app, db
from app.models import Permission, Role

app = create_app()


def seed_permissions():
    """Create all permissions organized by module"""

    permissions_data = [
        # =====================================================================
        # PATIENT MANAGEMENT PERMISSIONS
        # =====================================================================
        {
            'slug': 'patients.view',
            'name': 'View Patients',
            'description': 'View patient list and details',
            'category': 'patients'
        },
        {
            'slug': 'patients.read',
            'name': 'Read Patient Records',
            'description': 'Access patient medical records',
            'category': 'patients'
        },
        {
            'slug': 'patients.create',
            'name': 'Create Patient',
            'description': 'Register new patients',
            'category': 'patients'
        },
        {
            'slug': 'patients.write',
            'name': 'Write Patient Data',
            'description': 'Update patient information',
            'category': 'patients'
        },
        {
            'slug': 'patients.edit',
            'name': 'Edit Patient',
            'description': 'Modify patient details',
            'category': 'patients'
        },
        {
            'slug': 'patients.delete',
            'name': 'Delete Patient',
            'description': 'Remove patients from system',
            'category': 'patients'
        },

        # =====================================================================
        # APPOINTMENT MANAGEMENT PERMISSIONS
        # =====================================================================
        {
            'slug': 'appointments.view',
            'name': 'View Appointments',
            'description': 'View appointment list and details',
            'category': 'appointments'
        },
        {
            'slug': 'appointments.read',
            'name': 'Read Appointments',
            'description': 'Access appointment information',
            'category': 'appointments'
        },
        {
            'slug': 'appointments.create',
            'name': 'Create Appointment',
            'description': 'Book new appointments',
            'category': 'appointments'
        },
        {
            'slug': 'appointments.write',
            'name': 'Write Appointments',
            'description': 'Modify appointment data',
            'category': 'appointments'
        },
        {
            'slug': 'appointments.edit',
            'name': 'Edit Appointment',
            'description': 'Update appointment details',
            'category': 'appointments'
        },
        {
            'slug': 'appointments.cancel',
            'name': 'Cancel Appointment',
            'description': 'Cancel appointments',
            'category': 'appointments'
        },
        {
            'slug': 'appointments.view_own',
            'name': 'View Own Appointments',
            'description': 'View only assigned appointments',
            'category': 'appointments'
        },
        {
            'slug': 'appointments.delete',
            'name': 'Delete Appointments',
            'description': 'Remove appointments',
            'category': 'appointments'
        },

        # =====================================================================
        # CLINICAL/MEDICAL RECORDS PERMISSIONS
        # =====================================================================
        {
            'slug': 'clinical.view',
            'name': 'View Medical Records',
            'description': 'View patient medical history',
            'category': 'clinical'
        },
        {
            'slug': 'clinical.read',
            'name': 'Read Medical Records',
            'description': 'Access clinical documentation',
            'category': 'clinical'
        },
        {
            'slug': 'clinical.create',
            'name': 'Create Medical Record',
            'description': 'Document consultations',
            'category': 'clinical'
        },
        {
            'slug': 'clinical.write',
            'name': 'Write Medical Records',
            'description': 'Create and update clinical notes',
            'category': 'clinical'
        },
        {
            'slug': 'clinical.edit',
            'name': 'Edit Medical Record',
            'description': 'Update medical records',
            'category': 'clinical'
        },
        {
            'slug': 'clinical.view_own',
            'name': 'View Own Records',
            'description': 'View only own consultations',
            'category': 'clinical'
        },
        {
            'slug': 'clinical.delete',
            'name': 'Delete Medical Records',
            'description': 'Remove clinical documentation',
            'category': 'clinical'
        },

        # =====================================================================
        # FACILITY/BEDS PERMISSIONS
        # =====================================================================
        {
            'slug': 'facility.view',
            'name': 'View Beds',
            'description': 'View bed status and admissions',
            'category': 'facility'
        },
        {
            'slug': 'facility.read',
            'name': 'Read Facility Data',
            'description': 'Access bed and admission information',
            'category': 'facility'
        },
        {
            'slug': 'facility.admit',
            'name': 'Admit Patient',
            'description': 'Admit patients to beds',
            'category': 'facility'
        },
        {
            'slug': 'facility.write',
            'name': 'Write Facility Data',
            'description': 'Manage admissions',
            'category': 'facility'
        },
        {
            'slug': 'facility.discharge',
            'name': 'Discharge Patient',
            'description': 'Discharge patients',
            'category': 'facility'
        },
        {
            'slug': 'facility.manage_beds',
            'name': 'Manage Beds',
            'description': 'Change bed status',
            'category': 'facility'
        },
        {
            'slug': 'facility.delete',
            'name': 'Delete Admissions',
            'description': 'Remove admission records',
            'category': 'facility'
        },

        # =====================================================================
        # BILLING PERMISSIONS
        # =====================================================================
        {
            'slug': 'billing.view',
            'name': 'View Invoices',
            'description': 'View billing and invoices',
            'category': 'billing'
        },
        {
            'slug': 'billing.read',
            'name': 'Read Billing Data',
            'description': 'Access financial information',
            'category': 'billing'
        },
        {
            'slug': 'billing.create',
            'name': 'Create Invoice',
            'description': 'Generate new invoices',
            'category': 'billing'
        },
        {
            'slug': 'billing.write',
            'name': 'Write Billing Data',
            'description': 'Create and modify invoices',
            'category': 'billing'
        },
        {
            'slug': 'billing.process_payment',
            'name': 'Process Payment',
            'description': 'Record payments',
            'category': 'billing'
        },
        {
            'slug': 'billing.manage_services',
            'name': 'Manage Services',
            'description': 'Add/edit medical services',
            'category': 'billing'
        },
        {
            'slug': 'billing.delete',
            'name': 'Delete Invoices',
            'description': 'Cancel or remove invoices',
            'category': 'billing'
        },

        # =====================================================================
        # USER MANAGEMENT PERMISSIONS
        # =====================================================================
        {
            'slug': 'users.view',
            'name': 'View Users',
            'description': 'View user list',
            'category': 'users'
        },
        {
            'slug': 'users.read',
            'name': 'Read User Data',
            'description': 'Access user information',
            'category': 'users'
        },
        {
            'slug': 'users.create',
            'name': 'Create User',
            'description': 'Add new system users',
            'category': 'users'
        },
        {
            'slug': 'users.write',
            'name': 'Write User Data',
            'description': 'Manage user accounts',
            'category': 'users'
        },
        {
            'slug': 'users.edit',
            'name': 'Edit User',
            'description': 'Modify user details',
            'category': 'users'
        },
        {
            'slug': 'users.delete',
            'name': 'Delete User',
            'description': 'Remove users',
            'category': 'users'
        },
        {
            'slug': 'users.manage_roles',
            'name': 'Manage Roles',
            'description': 'Assign roles and permissions',
            'category': 'users'
        },

        # =====================================================================
        # REPORTS PERMISSIONS
        # =====================================================================
        {
            'slug': 'reports.view',
            'name': 'View Reports',
            'description': 'Access reports dashboard',
            'category': 'reports'
        },
        {
            'slug': 'reports.read',
            'name': 'Read Reports',
            'description': 'View system reports and analytics',
            'category': 'reports'
        },
        {
            'slug': 'reports.export',
            'name': 'Export Reports',
            'description': 'Export data to CSV/PDF',
            'category': 'reports'
        },
        {
            'slug': 'reports.advanced',
            'name': 'Advanced Reports',
            'description': 'Access advanced analytics',
            'category': 'reports'
        },

        # =====================================================================
        # ADMIN ACCESS PERMISSIONS
        # =====================================================================
        {
            'slug': 'admin.access',
            'name': 'Admin Access',
            'description': 'Access administration panel',
            'category': 'admin'
        },
        {
            'slug': 'admin.dashboard',
            'name': 'Admin Dashboard',
            'description': 'View admin dashboard',
            'category': 'admin'
        },
        {
            'slug': 'admin.manage_permissions',
            'name': 'Manage Permissions',
            'description': 'Configure system permissions',
            'category': 'admin'
        },
        {
            'slug': 'admin.system_settings',
            'name': 'System Settings',
            'description': 'Configure system settings',
            'category': 'admin'
        },
    ]

    created_perms = {}
    updated_count = 0
    created_count = 0

    for perm_data in permissions_data:
        perm = Permission.query.filter_by(slug=perm_data['slug']).first()
        if not perm:
            perm = Permission(
                slug=perm_data['slug'],
                name=perm_data['name'],
                description=perm_data['description'],
                category=perm_data['category']
            )
            db.session.add(perm)
            created_count += 1
            print(f'✓ Created: {perm_data["slug"]}')
        else:
            # Update existing permission details
            perm.name = perm_data['name']
            perm.description = perm_data['description']
            perm.category = perm_data['category']
            updated_count += 1

        created_perms[perm_data['slug']] = perm

    db.session.commit()

    return created_perms, created_count, updated_count


def assign_role_permissions():
    """Assign permissions to roles based on their responsibilities"""

    role_permissions_map = {
        'المشرف العام': [
            # Full access to everything
            'patients.view', 'patients.read', 'patients.create', 'patients.write',
            'patients.edit', 'patients.delete',

            'appointments.view', 'appointments.read', 'appointments.create',
            'appointments.write', 'appointments.edit', 'appointments.cancel', 'appointments.delete',

            'clinical.view', 'clinical.read', 'clinical.create', 'clinical.write',
            'clinical.edit', 'clinical.delete',

            'facility.view', 'facility.read', 'facility.admit', 'facility.write',
            'facility.discharge', 'facility.manage_beds', 'facility.delete',

            'billing.view', 'billing.read', 'billing.create', 'billing.write',
            'billing.process_payment', 'billing.manage_services', 'billing.delete',

            'users.view', 'users.read', 'users.create', 'users.write',
            'users.edit', 'users.delete', 'users.manage_roles',

            'reports.view', 'reports.read', 'reports.export', 'reports.advanced',

            'admin.access', 'admin.dashboard', 'admin.manage_permissions', 'admin.system_settings',
        ],

        'طبيب': [
            # Patient access
            'patients.view', 'patients.read',

            # Own appointments and clinical records
            'appointments.view_own', 'appointments.read', 'appointments.create',
            'appointments.edit',

            'clinical.view', 'clinical.read', 'clinical.create', 'clinical.write',
            'clinical.edit', 'clinical.view_own',

            # View facility
            'facility.view', 'facility.read',

            # View reports
            'reports.view', 'reports.read',
        ],

        'ممرض': [
            # Patient access
            'patients.view', 'patients.read',

            # View appointments
            'appointments.view', 'appointments.read',

            # View clinical records
            'clinical.view', 'clinical.read',

            # Full facility management
            'facility.view', 'facility.read', 'facility.admit', 'facility.write',
            'facility.discharge', 'facility.manage_beds',

            # View reports
            'reports.view', 'reports.read',
        ],

        'الاستقبال': [
            # Full patient management
            'patients.view', 'patients.read', 'patients.create', 'patients.write',
            'patients.edit', 'patients.delete',

            # Full appointment management
            'appointments.view', 'appointments.read', 'appointments.create',
            'appointments.write', 'appointments.edit', 'appointments.cancel',

            # Basic billing
            'billing.view', 'billing.read', 'billing.create',

            # View reports
            'reports.view', 'reports.read',
        ],

        'الفوترة': [
            # View patients
            'patients.view', 'patients.read',

            # Full billing access
            'billing.view', 'billing.read', 'billing.create', 'billing.write',
            'billing.process_payment', 'billing.manage_services', 'billing.delete',

            # Reports access
            'reports.view', 'reports.read', 'reports.export',
        ],
    }

    assignment_summary = {}

    for role_name, perm_slugs in role_permissions_map.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            print(f'⚠️  Warning: Role "{role_name}" not found. Skipping...')
            continue

        # Clear existing permissions
        role.permissions = []

        assigned_count = 0
        missing_perms = []

        for slug in perm_slugs:
            perm = Permission.query.filter_by(slug=slug).first()
            if perm:
                role.grant_permission(perm)
                assigned_count += 1
            else:
                missing_perms.append(slug)

        assignment_summary[role_name] = {
            'total': assigned_count,
            'expected': len(perm_slugs),
            'missing': missing_perms
        }

    db.session.commit()

    return assignment_summary


def main():
    with app.app_context():
        print('=' * 70)
        print('🔧 COMPREHENSIVE PERMISSION SEEDING')
        print('=' * 70)
        print()

        # Check if roles exist
        role_count = Role.query.count()
        if role_count == 0:
            print('❌ ERROR: No roles found in database!')
            print('   Please run "python init_db.py" first to create roles.')
            print()
            return

        print(f'✓ Found {role_count} roles in database')
        print()

        # Step 1: Create/Update Permissions
        print('📝 Step 1: Creating/Updating Permissions...')
        print('-' * 70)
        perms, created, updated = seed_permissions()

        if created > 0:
            print(f'\n✓ Created: {created} new permissions')
        if updated > 0:
            print(f'✓ Updated: {updated} existing permissions')

        print(f'✓ Total: {len(perms)} permissions in system')
        print()

        # Show permissions by category
        categories = {}
        for slug, perm in perms.items():
            if perm.category not in categories:
                categories[perm.category] = []
            categories[perm.category].append(slug)

        print('📊 Permissions by Category:')
        for category, perm_list in sorted(categories.items()):
            print(f'   • {category}: {len(perm_list)} permissions')
        print()

        # Step 2: Assign to Roles
        print('👥 Step 2: Assigning Permissions to Roles...')
        print('-' * 70)
        assignments = assign_role_permissions()

        all_success = True
        for role_name, counts in assignments.items():
            if counts['total'] == counts['expected']:
                print(f'✓ {role_name}: {counts["total"]} permissions assigned')
            else:
                all_success = False
                print(f'⚠️  {role_name}: {counts["total"]}/{counts["expected"]} permissions')
                if counts['missing']:
                    print(f'   Missing: {", ".join(counts["missing"][:3])}...')
        print()

        # Step 3: Verification
        print('🔍 Step 3: Verification...')
        print('-' * 70)

        # Check Super Admin
        admin_role = Role.query.filter_by(name='Super Admin').first()
        if admin_role:
            admin_perms = len(admin_role.permissions)
            print(f'✓ Super Admin has {admin_perms} permissions')

            # Check critical permissions
            critical = ['admin.access', 'users.manage_roles', 'reports.advanced']
            has_all = all(admin_role.has_permission(p) for p in critical)
            if has_all:
                print('✓ Super Admin has all critical permissions')
            else:
                print('⚠️  Warning: Super Admin missing some critical permissions')

        # Check other roles
        for role_name in ['Doctor', 'Nurse', 'Reception', 'Billing']:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                print(f'✓ {role_name}: {len(role.permissions)} permissions')

        print()
        print('=' * 70)
        if all_success:
            print('✅ PERMISSION SEEDING COMPLETED SUCCESSFULLY!')
        else:
            print('⚠️  PERMISSION SEEDING COMPLETED WITH WARNINGS')
        print('=' * 70)
        print()
        print('📋 Summary:')
        print(f'   • Total Permissions: {len(perms)}')
        print(f'   • Roles Configured: {len(assignments)}')
        print(f'   • Categories: {len(categories)}')
        print()
        print('🎯 Next Steps:')
        print('   1. Restart your Flask application')
        print('   2. Test admin access at /admin')
        print('   3. Test reports access at /reports')
        print('   4. Verify role-based access control')
        print()
        print('💡 Tips:')
        print('   • Admin users can see the "الإدارة" (Administration) menu')
        print('   • Check permissions with: user.can("permission.slug")')
        print('   • Manage roles at: /admin/roles')
        print()


if __name__ == '__main__':
    main()