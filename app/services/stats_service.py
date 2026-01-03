# app/services/stats_service.py - Enhanced with date filtering

from datetime import datetime, timedelta, date
from sqlalchemy import func, extract, and_, or_, Date, cast, case
from app import db
from app.models import (
    Invoice, InvoiceStatus, Patient, Appointment, AppointmentStatus,
    Bed, BedStatus, Admission, AdmissionStatus, Service, User, MedicalVisit
)
from decimal import Decimal


class StatsService:
    """Enhanced service class with date range filtering support"""

    # ========================================================================
    # REVENUE STATISTICS (with date filtering)
    # ========================================================================

    @staticmethod
    def get_revenue_stats(start_date=None, end_date=None):
        """
        Get revenue statistics for a date range.
        If no dates provided, uses current month.
        """
        now = datetime.now()

        # Default to current month if no dates provided
        if not start_date:
            start_date = date(now.year, now.month, 1)
        if not end_date:
            end_date = now.date()

        # Calculate previous period for comparison
        period_days = (end_date - start_date).days + 1
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_days - 1)

        # Query for paid invoices in current period
        current_revenue = db.session.query(
            func.coalesce(func.sum(Invoice.total_amount), 0)
        ).filter(
            Invoice.status == InvoiceStatus.paid,
            func.cast(Invoice.paid_at, Date) >= start_date,
            func.cast(Invoice.paid_at, Date) <= end_date
        ).scalar() or Decimal('0')

        # Query for previous period
        previous_revenue = db.session.query(
            func.coalesce(func.sum(Invoice.total_amount), 0)
        ).filter(
            Invoice.status == InvoiceStatus.paid,
            func.cast(Invoice.paid_at, Date) >= prev_start,
            func.cast(Invoice.paid_at, Date) <= prev_end
        ).scalar() or Decimal('0')

        # Calculate growth
        growth = StatsService._calculate_growth(current_revenue, previous_revenue)

        # Get invoice count
        invoice_count = Invoice.query.filter(
            Invoice.status == InvoiceStatus.paid,
            func.cast(Invoice.paid_at, Date) >= start_date,
            func.cast(Invoice.paid_at, Date) <= end_date
        ).count()

        return {
            'total': float(current_revenue),
            'previous_period': float(previous_revenue),
            'growth': growth,
            'invoice_count': invoice_count,
            'period_days': period_days
        }

    @staticmethod
    def get_revenue_by_month(months=12):
        """Get revenue for the last N months (always 12 months trend)"""
        now = datetime.now()
        results = []

        for i in range(months - 1, -1, -1):
            target_month = now.month - i
            target_year = now.year

            while target_month <= 0:
                target_month += 12
                target_year -= 1

            month_start = date(target_year, target_month, 1)
            if target_month == 12:
                next_month = date(target_year + 1, 1, 1)
            else:
                next_month = date(target_year, target_month + 1, 1)

            month_data = db.session.query(
                func.coalesce(func.sum(Invoice.total_amount), 0).label('revenue'),
                func.count(Invoice.id).label('count')
            ).filter(
                Invoice.status == InvoiceStatus.paid,
                func.cast(Invoice.paid_at, Date) >= month_start,
                func.cast(Invoice.paid_at, Date) < next_month
            ).first()

            month_names_ar = [
                'يناير', 'فبراير', 'مارس', 'إبريل', 'مايو', 'يونيو',
                'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
            ]

            results.append({
                'month': f'{target_year}-{target_month:02d}',
                'month_name': f'{month_names_ar[target_month - 1]} {target_year}',
                'revenue': float(month_data.revenue),
                'invoice_count': month_data.count
            })

        return results

    # ========================================================================
    # PATIENT STATISTICS (with date filtering)
    # ========================================================================

    @staticmethod
    def get_patient_stats(start_date=None, end_date=None):
        """Get patient statistics for date range"""
        now = datetime.now()

        if not start_date:
            start_date = date(now.year, now.month, 1)
        if not end_date:
            end_date = now.date()

        # Total patients (all time)
        total = Patient.query.count()

        # New patients in period
        new_in_period = Patient.query.filter(
            func.cast(Patient.created_at, Date) >= start_date,
            func.cast(Patient.created_at, Date) <= end_date
        ).count()

        # Gender distribution (all time)
        gender_stats = db.session.query(
            Patient.gender,
            func.count(Patient.id)
        ).group_by(Patient.gender).all()

        by_gender = {'M': 0, 'F': 0, 'unknown': 0}
        for gender, count in gender_stats:
            if gender == 'M':
                by_gender['M'] = count
            elif gender == 'F':
                by_gender['F'] = count
            else:
                by_gender['unknown'] += count

        return {
            'total': total,
            'new_in_period': new_in_period,
            'by_gender': by_gender
        }

    @staticmethod
    def get_patients_by_month(months=12):
        """Get patient registrations by month (last 12 months)"""
        now = datetime.now()
        results = []

        for i in range(months - 1, -1, -1):
            target_month = now.month - i
            target_year = now.year

            while target_month <= 0:
                target_month += 12
                target_year -= 1

            count = db.session.query(func.count(Patient.id)).filter(
                extract('year', Patient.created_at) == target_year,
                extract('month', Patient.created_at) == target_month
            ).scalar()

            month_names_ar = [
                'يناير', 'فبراير', 'مارس', 'إبريل', 'مايو', 'يونيو',
                'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
            ]

            results.append({
                'month': f'{target_year}-{target_month:02d}',
                'month_name': f'{month_names_ar[target_month - 1]} {target_year}',
                'count': count
            })

        return results

    # ========================================================================
    # APPOINTMENT STATISTICS (with date filtering)
    # ========================================================================

    @staticmethod
    def get_appointment_stats(start_date=None, end_date=None):
        """Get appointment statistics for date range"""
        now = datetime.now()

        if not start_date:
            start_date = date(now.year, now.month, 1)
        if not end_date:
            end_date = now.date()

        # Count by status in period
        status_counts = db.session.query(
            Appointment.status,
            func.count(Appointment.id)
        ).filter(
            func.cast(Appointment.date_time, Date) >= start_date,
            func.cast(Appointment.date_time, Date) <= end_date
        ).group_by(Appointment.status).all()

        by_status = {
            'pending': 0,
            'confirmed': 0,
            'completed': 0,
            'cancelled': 0,
            'no_show': 0
        }

        total = 0
        for status, count in status_counts:
            by_status[status.value] = count
            total += count

        # Completion rate
        completed = by_status['completed']
        total_actionable = completed + by_status['cancelled'] + by_status['no_show']
        completion_rate = (completed / total_actionable * 100) if total_actionable > 0 else 0

        return {
            'total': total,
            'by_status': by_status,
            'completion_rate': round(completion_rate, 1)
        }

    @staticmethod
    def get_appointments_by_doctor(start_date=None, end_date=None):
        """Get appointment counts by doctor for date range"""
        now = datetime.now()

        if not start_date:
            start_date = date(now.year, now.month, 1)
        if not end_date:
            end_date = now.date()

        results = db.session.query(
            User.id,
            User.full_name_ar,
            func.count(Appointment.id).label('total'),
            func.sum(
                case((Appointment.status == AppointmentStatus.completed, 1), else_=0)
            ).label('completed'),
            func.sum(
                case(
                    (Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed]), 1),
                    else_=0
                )
            ).label('pending')
        ).join(
            Appointment, User.id == Appointment.doctor_id
        ).filter(
            func.cast(Appointment.date_time, Date) >= start_date,
            func.cast(Appointment.date_time, Date) <= end_date
        ).group_by(
            User.id, User.full_name_ar
        ).order_by(
            func.count(Appointment.id).desc()
        ).all()

        return [{
            'doctor_id': r.id,
            'doctor_name': r.full_name_ar,
            'total': r.total,
            'completed': r.completed or 0,
            'pending': r.pending or 0
        } for r in results]

    # ========================================================================
    # BED/FACILITY STATISTICS
    # ========================================================================

    @staticmethod
    def get_bed_occupancy():
        """Get current bed occupancy (real-time, not date filtered)"""
        status_counts = db.session.query(
            Bed.status,
            func.count(Bed.id)
        ).group_by(Bed.status).all()

        stats = {
            'total_beds': 0,
            'occupied': 0,
            'available': 0,
            'maintenance': 0
        }

        for status, count in status_counts:
            stats['total_beds'] += count
            if status == BedStatus.occupied:
                stats['occupied'] = count
            elif status == BedStatus.available:
                stats['available'] = count
            elif status == BedStatus.maintenance:
                stats['maintenance'] = count

        occupancy_rate = (stats['occupied'] / stats['total_beds'] * 100) if stats['total_beds'] > 0 else 0
        stats['occupancy_rate'] = round(occupancy_rate, 1)

        return stats

    @staticmethod
    def get_admission_stats(start_date=None, end_date=None):
        """Get admission statistics for date range"""
        now = datetime.now()

        if not start_date:
            start_date = date(now.year, now.month, 1)
        if not end_date:
            end_date = now.date()

        # Active admissions (current)
        active = Admission.query.filter_by(status=AdmissionStatus.active).count()

        # Admissions in period
        admissions_in_period = Admission.query.filter(
            func.cast(Admission.admission_date, Date) >= start_date,
            func.cast(Admission.admission_date, Date) <= end_date
        ).count()

        # Average stay duration (discharged in period)
        discharged = Admission.query.filter(
            Admission.status == AdmissionStatus.discharged,
            func.cast(Admission.discharge_date, Date) >= start_date,
            func.cast(Admission.discharge_date, Date) <= end_date,
            Admission.discharge_date.isnot(None)
        ).all()

        if discharged:
            total_days = sum([
                (adm.discharge_date - adm.admission_date).days
                for adm in discharged
            ])
            avg_stay = total_days / len(discharged)
        else:
            avg_stay = 0

        return {
            'active_admissions': active,
            'total_in_period': admissions_in_period,
            'avg_stay_duration': round(avg_stay, 1)
        }

    # ========================================================================
    # SERVICE STATISTICS (with date filtering)
    # ========================================================================

    @staticmethod
    def get_top_services(limit=10, start_date=None, end_date=None):
        """Get most used services for date range"""
        from app.models import InvoiceItem

        now = datetime.now()

        if not start_date:
            start_date = date(now.year, now.month, 1)
        if not end_date:
            end_date = now.date()

        results = db.session.query(
            InvoiceItem.service_name,
            func.count(InvoiceItem.id).label('usage_count'),
            func.sum(InvoiceItem.cost * InvoiceItem.quantity).label('revenue')
        ).join(
            Invoice, InvoiceItem.invoice_id == Invoice.id
        ).filter(
            func.cast(Invoice.created_at, Date) >= start_date,
            func.cast(Invoice.created_at, Date) <= end_date
        ).group_by(
            InvoiceItem.service_name
        ).order_by(
            func.count(InvoiceItem.id).desc()
        ).limit(limit).all()

        return [{
            'service_name': r.service_name,
            'usage_count': r.usage_count,
            'total_revenue': float(r.revenue)
        } for r in results]

    # ========================================================================
    # COMPREHENSIVE DASHBOARD DATA
    # ========================================================================

    @staticmethod
    def get_dashboard_stats(start_date=None, end_date=None):
        """Get comprehensive statistics for dashboard with date filtering"""
        return {
            # Filtered by date range
            'revenue': StatsService.get_revenue_stats(start_date, end_date),
            'patients': StatsService.get_patient_stats(start_date, end_date),
            'appointments': StatsService.get_appointment_stats(start_date, end_date),
            'appointments_by_doctor': StatsService.get_appointments_by_doctor(start_date, end_date),
            'admissions': StatsService.get_admission_stats(start_date, end_date),
            'top_services': StatsService.get_top_services(10, start_date, end_date),

            # Always 12-month trends (not filtered)
            'revenue_by_month': StatsService.get_revenue_by_month(12),
            'patients_by_month': StatsService.get_patients_by_month(12),

            # Real-time status (not filtered)
            'bed_occupancy': StatsService.get_bed_occupancy(),
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    @staticmethod
    def _calculate_growth(current, previous):
        """Calculate growth percentage"""
        if previous == 0 or previous is None:
            return 100.0 if current > 0 else 0.0

        growth = ((float(current) - float(previous)) / float(previous)) * 100
        return round(growth, 1)