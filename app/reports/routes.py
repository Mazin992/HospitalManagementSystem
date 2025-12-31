# app/reports/routes.py - Enhanced with better date filtering

from flask import render_template, request, jsonify
from flask_login import login_required
from app.reports import bp
from app.reports.forms import DateRangeFilterForm
from app.services.stats_service import StatsService
from app.decorators import permission_required
from datetime import datetime, timedelta, date
from calendar import monthrange


def calculate_date_range(preset):
    """Calculate start and end dates based on preset range"""
    today = date.today()

    if preset == 'today':
        return today, today

    elif preset == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday

    elif preset == 'this_week':
        start = today - timedelta(days=today.weekday())
        return start, today

    elif preset == 'last_week':
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        return last_monday, last_sunday

    elif preset == 'this_month':
        start = date(today.year, today.month, 1)
        return start, today

    elif preset == 'last_month':
        if today.month == 1:
            start = date(today.year - 1, 12, 1)
            _, last_day = monthrange(today.year - 1, 12)
            end = date(today.year - 1, 12, last_day)
        else:
            start = date(today.year, today.month - 1, 1)
            _, last_day = monthrange(today.year, today.month - 1)
            end = date(today.year, today.month - 1, last_day)
        return start, end

    elif preset == 'this_quarter':
        quarter = (today.month - 1) // 3
        start = date(today.year, quarter * 3 + 1, 1)
        return start, today

    elif preset == 'this_year':
        start = date(today.year, 1, 1)
        return start, today

    elif preset == 'last_year':
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)
        return start, end

    else:  # Default: this month
        start = date(today.year, today.month, 1)
        return start, today


@bp.route('/')
@bp.route('/dashboard')
@login_required
@permission_required('reports', 'read')
def dashboard():
    """Enhanced reports dashboard with flexible date filtering"""

    form = DateRangeFilterForm()

    # Get filter parameters from request
    preset_range = request.args.get('preset_range', 'this_month')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Determine date range
    if start_date_str and end_date_str:
        # Custom dates provided
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            preset_range = 'custom'
        except ValueError:
            # Invalid dates, use preset
            start_date, end_date = calculate_date_range(preset_range)
    else:
        # Use preset
        start_date, end_date = calculate_date_range(preset_range)

    # Update form with current values
    form.start_date.data = start_date
    form.end_date.data = end_date
    form.preset_range.data = preset_range

    # Get filtered statistics
    stats = StatsService.get_dashboard_stats(start_date, end_date)

    # Format period description for display
    if preset_range == 'today':
        period_desc = 'اليوم'
    elif preset_range == 'yesterday':
        period_desc = 'أمس'
    elif preset_range == 'this_week':
        period_desc = 'هذا الأسبوع'
    elif preset_range == 'last_week':
        period_desc = 'الأسبوع الماضي'
    elif preset_range == 'this_month':
        period_desc = 'هذا الشهر'
    elif preset_range == 'last_month':
        period_desc = 'الشهر الماضي'
    elif preset_range == 'this_quarter':
        period_desc = 'هذا الربع'
    elif preset_range == 'this_year':
        period_desc = 'هذا العام'
    elif preset_range == 'last_year':
        period_desc = 'العام الماضي'
    else:
        period_desc = f'من {start_date.strftime("%Y-%m-%d")} إلى {end_date.strftime("%Y-%m-%d")}'

    return render_template(
        'reports/dashboard.html',
        form=form,
        stats=stats,
        start_date=start_date,
        end_date=end_date,
        preset_range=preset_range,
        period_desc=period_desc
    )


# API endpoints remain the same but could be enhanced if needed
@bp.route('/api/revenue-data')
@login_required
@permission_required('reports', 'read')
def api_revenue_data():
    """API endpoint for revenue chart data (always 12 months)"""
    revenue_data = StatsService.get_revenue_by_month(12)

    return jsonify({
        'labels': [item['month_name'] for item in revenue_data],
        'data': [item['revenue'] for item in revenue_data],
        'invoice_counts': [item['invoice_count'] for item in revenue_data]
    })


@bp.route('/api/patients-data')
@login_required
@permission_required('reports', 'read')
def api_patients_data():
    """API endpoint for patient registration chart data (always 12 months)"""
    patient_data = StatsService.get_patients_by_month(12)

    return jsonify({
        'labels': [item['month_name'] for item in patient_data],
        'data': [item['count'] for item in patient_data]
    })