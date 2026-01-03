from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
import enum

# ============================================================================
# ENUMS
# ============================================================================
class AppointmentStatus(enum.Enum):
    pending = 'pending'
    confirmed = 'confirmed'
    completed = 'completed'
    cancelled = 'cancelled'
    no_show = 'no_show'

class BedStatus(enum.Enum):
    available = 'available'
    occupied = 'occupied'
    maintenance = 'maintenance'

class InvoiceStatus(enum.Enum):
    unpaid = 'unpaid'
    paid = 'paid'
    insurance_pending = 'insurance_pending'

class AdmissionStatus(enum.Enum):
    active = 'active'
    discharged = 'discharged'


# ============================================================================
# AUTHORIZATION MODELS (NEW)
# ============================================================================

# Many-to-many association table for roles and permissions
roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
                             db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True),
                             db.Column('granted_at', db.DateTime, default=datetime.utcnow)
                             )


class Permission(db.Model):
    """Granular permissions for system access control"""
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Human-readable name (e.g., "View Patients")
    slug = db.Column(db.String(100), unique=True, nullable=False,
                     index=True)  # Unique identifier (e.g., "patients.view")
    description = db.Column(db.String(255))  # What this permission allows
    category = db.Column(db.String(50))  # Grouping (e.g., "patients", "billing", "clinical")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to roles (many-to-many)
    roles = db.relationship('Role', secondary=roles_permissions, back_populates='permissions')

    def __repr__(self):
        return f'<Permission {self.slug}>'


class Role(db.Model):
    """User roles with granular permissions"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))  # What this role does
    is_system_role = db.Column(db.Boolean, default=False)  # Cannot be deleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship('User', backref='role', lazy='dynamic')
    permissions = db.relationship('Permission', secondary=roles_permissions, back_populates='roles')

    def has_permission(self, permission_slug):
        """Check if this role has a specific permission"""
        return any(perm.slug == permission_slug for perm in self.permissions)

    def grant_permission(self, permission):
        """Grant a permission to this role"""
        if permission not in self.permissions:
            self.permissions.append(permission)

    def revoke_permission(self, permission):
        """Revoke a permission from this role"""
        if permission in self.permissions:
            self.permissions.remove(permission)

    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    """System users with role-based permissions"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name_ar = db.Column(db.String(200), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)  # Track last login
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    appointments_as_doctor = db.relationship('Appointment', backref='doctor', lazy='dynamic')
    medical_visits = db.relationship('MedicalVisit', backref='doctor', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, permission_slug):
        """
        Check if user has a specific permission via their role.
        Returns True if user's role has the permission, False otherwise.

        Usage:
            if current_user.can('patients.create'):
                # allow action
        """
        if not self.role:
            return False
        return self.role.has_permission(permission_slug)

    def has_any_permission(self, *permission_slugs):
        """Check if user has ANY of the provided permissions"""
        return any(self.can(slug) for slug in permission_slugs)

    def has_all_permissions(self, *permission_slugs):
        """Check if user has ALL of the provided permissions"""
        return all(self.can(slug) for slug in permission_slugs)

    # Keep backward compatibility with old method
    def has_permission(self, resource, action):
        """
        DEPRECATED: Backward compatibility method.
        Use can('resource.action') instead.
        """
        permission_slug = f"{resource}.{action}"
        return self.can(permission_slug)

    def __repr__(self):
        return f'<User {self.username}>'

# ============================================================================
# PATIENT MANAGEMENT
# ============================================================================
class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(200), nullable=False)  # Arabic name
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(1))  # M/F
    dob = db.Column(db.Date)
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    admissions = db.relationship('Admission', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Patient {self.file_number}: {self.full_name}>'


# ============================================================================
# CLINICAL (APPOINTMENTS & RECORDS)
# ============================================================================
class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.pending, nullable=False)
    type = db.Column(db.String(20), default='scheduled')  # walk-in, scheduled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    medical_visit = db.relationship('MedicalVisit', backref='appointment', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Appointment {self.id}: Patient {self.patient_id} on {self.date_time}>'


class MedicalVisit(db.Model):
    __tablename__ = 'medical_visits'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), unique=True, nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symptoms = db.Column(db.Text)  # Arabic text
    diagnosis = db.Column(db.Text)  # Arabic text
    prescription_text = db.Column(db.Text)  # Arabic text
    vitals = db.Column(JSON)  # {"temp": 37.5, "bp": "120/80", "weight": 70}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MedicalVisit {self.id} for Appointment {self.appointment_id}>'


# ============================================================================
# FACILITY (ROOMS & BEDS)
# ============================================================================
class Bed(db.Model):
    __tablename__ = 'beds'
    
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), nullable=False)
    bed_label = db.Column(db.String(10), nullable=False)  # e.g., 'A1', 'B2'
    status = db.Column(db.Enum(BedStatus), default=BedStatus.available, nullable=False)
    
    # Relationships
    admissions = db.relationship('Admission', backref='bed', lazy='dynamic')
    
    __table_args__ = (
        db.UniqueConstraint('room_number', 'bed_label', name='uq_room_bed'),
    )
    
    def __repr__(self):
        return f'<Bed {self.room_number}-{self.bed_label}: {self.status.value}>'


class Admission(db.Model):
    __tablename__ = 'admissions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=False)
    admission_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    discharge_date = db.Column(db.DateTime)
    status = db.Column(db.Enum(AdmissionStatus), default=AdmissionStatus.active, nullable=False)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Admission {self.id}: Patient {self.patient_id} in Bed {self.bed_id}>'


# ============================================================================
# BILLING
# ============================================================================
class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(200), nullable=False)  # Arabic service name
    cost_sdg = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Service {self.name_ar}: {self.cost_sdg} SDG>'


class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(InvoiceStatus), default=InvoiceStatus.unpaid, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    # Relationships
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Invoice {self.id}: {self.total_amount} SDG>'


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    service_name = db.Column(db.String(200), nullable=False)  # Arabic
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f'<InvoiceItem {self.service_name}: {self.cost} SDG>'