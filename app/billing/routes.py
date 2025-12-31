

from flask import render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from app.billing import bp
from app.billing.forms import ServiceForm, CreateInvoiceForm, PaymentForm
from app.models import Service, Invoice, InvoiceItem, Patient, InvoiceStatus
from app.decorators import role_required, permission_required
from app import db
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, desc, cast, String

# ============================================================================
# SERVICE MANAGEMENT
# ============================================================================
@bp.route('/services')
@login_required
@role_required('Super Admin', 'Billing')
def services_list():
    """List all services"""
    services = Service.query.order_by(Service.name_ar).all()
    
    active_count = sum(1 for s in services if s.is_active)
    inactive_count = len(services) - active_count
    
    return render_template(
        'billing/services_list.html',
        services=services,
        active_count=active_count,
        inactive_count=inactive_count
    )


@bp.route('/services/new', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin')
def create_service():
    """Create new service"""
    form = ServiceForm()
    
    if form.validate_on_submit():
        service = Service(
            name_ar=form.name_ar.data.strip(),
            cost_sdg=form.cost_sdg.data,
            is_active=form.is_active.data
        )
        
        try:
            db.session.add(service)
            db.session.commit()
            flash(f'تم إضافة الخدمة "{service.name_ar}" بنجاح.', 'success')
            return redirect(url_for('billing.services_list'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إضافة الخدمة. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('billing/service_form.html', form=form, title='إضافة خدمة جديدة')


@bp.route('/services/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin')
def edit_service(service_id):
    """Edit existing service"""
    service = Service.query.get_or_404(service_id)
    form = ServiceForm(obj=service)
    
    if form.validate_on_submit():
        service.name_ar = form.name_ar.data.strip()
        service.cost_sdg = form.cost_sdg.data
        service.is_active = form.is_active.data
        
        try:
            db.session.commit()
            flash(f'تم تحديث الخدمة "{service.name_ar}" بنجاح.', 'success')
            return redirect(url_for('billing.services_list'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء التحديث. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('billing/service_form.html', form=form, title='تعديل الخدمة', service=service)


@bp.route('/services/<int:service_id>/toggle', methods=['POST'])
@login_required
@role_required('Super Admin')
def toggle_service(service_id):
    """Toggle service active status"""
    service = Service.query.get_or_404(service_id)
    service.is_active = not service.is_active
    
    try:
        db.session.commit()
        status = 'تفعيل' if service.is_active else 'إلغاء تفعيل'
        flash(f'تم {status} الخدمة "{service.name_ar}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ. يرجى المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('billing.services_list'))


# ============================================================================
# INVOICE MANAGEMENT
# ============================================================================
@bp.route('/invoices')
@login_required
@permission_required('billing', 'read')
def invoices_list():
    """List all invoices with filters"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '').strip()
    
    # Base query
    query = Invoice.query
    
    # Apply status filter
    if status_filter != 'all':
        query = query.filter_by(status=InvoiceStatus[status_filter])
    
    # Apply search filter
    if search_query:
        query = query.join(Patient).filter(
            db.or_(
                Patient.full_name.ilike(f'%{search_query}%'),
                Patient.file_number.ilike(f'%{search_query}%'),
                cast(Invoice.id, String).ilike(f'%{search_query}%')
            )
        )
    
    # Pagination
    invoices = query.order_by(desc(Invoice.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistics
    total_unpaid = Invoice.query.filter_by(status=InvoiceStatus.unpaid).count()
    total_paid = Invoice.query.filter_by(status=InvoiceStatus.paid).count()
    total_insurance = Invoice.query.filter_by(status=InvoiceStatus.insurance_pending).count()
    
    # Revenue statistics
    total_revenue = db.session.query(func.sum(Invoice.total_amount)).filter_by(
        status=InvoiceStatus.paid
    ).scalar() or Decimal('0')
    
    pending_amount = db.session.query(func.sum(Invoice.total_amount)).filter_by(
        status=InvoiceStatus.unpaid
    ).scalar() or Decimal('0')
    
    return render_template(
        'billing/invoices_list.html',
        invoices=invoices,
        status_filter=status_filter,
        search_query=search_query,
        total_unpaid=total_unpaid,
        total_paid=total_paid,
        total_insurance=total_insurance,
        total_revenue=total_revenue,
        pending_amount=pending_amount
    )


@bp.route('/invoices/create', methods=['GET', 'POST'])
@login_required
@permission_required('billing', 'write')
def create_invoice():
    """Create new invoice"""
    form = CreateInvoiceForm()
    
    if form.validate_on_submit():
        patient_id = form.patient_id.data
        
        # Validate at least one service
        valid_items = [item for item in form.services.data if item['service_id'] > 0]
        if not valid_items:
            flash('يجب إضافة خدمة واحدة على الأقل.', 'warning')
            return render_template('billing/create_invoice.html', form=form)
        
        # Calculate total
        total_amount = Decimal('0')
        invoice_items = []
        
        for item_data in valid_items:
            service = Service.query.get(item_data['service_id'])
            if service:
                quantity = item_data['quantity']
                item_cost = service.cost_sdg * quantity
                total_amount += item_cost
                
                invoice_items.append({
                    'service_name': service.name_ar,
                    'cost': service.cost_sdg,
                    'quantity': quantity
                })
        
        # Create invoice
        invoice = Invoice(
            patient_id=patient_id,
            total_amount=total_amount,
            status=InvoiceStatus.unpaid
        )
        
        try:
            db.session.add(invoice)
            db.session.flush()  # Get invoice ID
            
            # Create invoice items
            for item_data in invoice_items:
                invoice_item = InvoiceItem(
                    invoice_id=invoice.id,
                    service_name=item_data['service_name'],
                    cost=item_data['cost'],
                    quantity=item_data['quantity']
                )
                db.session.add(invoice_item)
            
            db.session.commit()
            flash(f'تم إنشاء الفاتورة #{invoice.id} بنجاح. المبلغ الإجمالي: {float(total_amount):.2f} ج.س', 'success')
            return redirect(url_for('billing.invoice_detail', invoice_id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إنشاء الفاتورة. يرجى المحاولة مرة أخرى.', 'danger')
    
    # Get services for JavaScript
    services = Service.query.filter_by(is_active=True).order_by(Service.name_ar).all()
    services_data = [{'id': s.id, 'name': s.name_ar, 'cost': float(s.cost_sdg)} for s in services]
    
    return render_template('billing/create_invoice.html', form=form, services_data=services_data)


@bp.route('/invoices/<int:invoice_id>')
@login_required
@permission_required('billing', 'read')
def invoice_detail(invoice_id):
    """View invoice details"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    return render_template('billing/invoice_detail.html', invoice=invoice)


@bp.route('/invoices/<int:invoice_id>/pay', methods=['GET', 'POST'])
@login_required
@permission_required('billing', 'write')
def pay_invoice(invoice_id):
    """Record payment for invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check if already paid
    if invoice.status == InvoiceStatus.paid:
        flash('هذه الفاتورة مدفوعة بالفعل.', 'info')
        return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))
    
    form = PaymentForm()
    
    # Pre-fill amount
    if request.method == 'GET':
        form.amount_paid.data = invoice.total_amount
    
    if form.validate_on_submit():
        amount_paid = form.amount_paid.data
        
        # Validate amount
        if amount_paid < invoice.total_amount:
            flash(f'المبلغ المدفوع ({float(amount_paid):.2f} ج.س) أقل من المبلغ المطلوب ({float(invoice.total_amount):.2f} ج.س).', 'warning')
            return render_template('billing/payment_form.html', form=form, invoice=invoice)
        
        # Update invoice status
        payment_method = form.payment_method.data
        
        if payment_method == 'insurance':
            invoice.status = InvoiceStatus.insurance_pending
        else:
            invoice.status = InvoiceStatus.paid
            invoice.paid_at = datetime.utcnow()
        
        # Store payment info in notes (simple approach)
        payment_info = f"\n[دفعة - {datetime.now().strftime('%Y-%m-%d %H:%M')}]\n"
        payment_info += f"الطريقة: {dict(form.payment_method.choices)[payment_method]}\n"
        payment_info += f"المبلغ: {float(amount_paid):.2f} ج.س\n"
        if form.reference_number.data:
            payment_info += f"المرجع: {form.reference_number.data}\n"
        if form.notes.data:
            payment_info += f"ملاحظات: {form.notes.data}\n"
        
        # You could create a separate Payment model, but for simplicity we'll note it here
        
        try:
            db.session.commit()
            
            if invoice.status == InvoiceStatus.paid:
                flash(f'تم تسجيل الدفعة بنجاح. الفاتورة #{invoice.id} مدفوعة.', 'success')
            else:
                flash(f'تم تسجيل الفاتورة #{invoice.id} كـ "معلقة على التأمين".', 'info')
            
            return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تسجيل الدفعة. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('billing/payment_form.html', form=form, invoice=invoice)


@bp.route('/invoices/<int:invoice_id>/print')
@login_required
@permission_required('billing', 'read')
def print_receipt(invoice_id):
    """Print-friendly receipt"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Get hospital info from config
    from flask import current_app
    hospital_name = "مستشفى السلام العام"  # Could be from config
    hospital_address = "الخرطوم، السودان"
    hospital_phone = "+249 123 456 789"
    
    response = make_response(render_template(
        'billing/receipt.html',
        invoice=invoice,
        hospital_name=hospital_name,
        hospital_address=hospital_address,
        hospital_phone=hospital_phone
    ))
    
    return response


@bp.route('/invoices/<int:invoice_id>/cancel', methods=['POST'])
@login_required
@permission_required('billing', 'delete')
def cancel_invoice(invoice_id):
    """Cancel an unpaid invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.status == InvoiceStatus.paid:
        flash('لا يمكن إلغاء فاتورة مدفوعة.', 'danger')
        return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))
    
    try:
        # Instead of deleting, we could add a 'cancelled' status
        # For now, we'll delete the invoice and its items
        db.session.delete(invoice)
        db.session.commit()
        flash(f'تم إلغاء الفاتورة #{invoice_id}.', 'success')
        return redirect(url_for('billing.invoices_list'))
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء الإلغاء. يرجى المحاولة مرة أخرى.', 'danger')
        return redirect(url_for('billing.invoice_detail', invoice_id=invoice_id))