from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from models import db, Payroll, Employee
from datetime import datetime, date
from rbac import can_manage_payroll, get_team_employee_ids

payroll_bp = Blueprint('payroll', __name__, url_prefix='/payroll')


@payroll_bp.route('/')
@login_required
def list_payroll():
    if current_user.role == 'employee':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        if emp:
            payrolls = Payroll.query.filter_by(employee_id=emp.id).order_by(
                Payroll.year.desc(), Payroll.month.desc()
            ).all()
        else:
            payrolls = []
    elif current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids:
            payrolls = Payroll.query.filter(
                Payroll.employee_id.in_(team_ids)
            ).order_by(Payroll.year.desc(), Payroll.month.desc()).all()
        else:
            payrolls = []
    else:
        payrolls = Payroll.query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()

    return render_template('payroll.html', payrolls=payrolls)


@payroll_bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_payroll():
    if not can_manage_payroll(current_user):
        abort(403)

    employees = Employee.query.all()

    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        month = int(request.form.get('month'))
        year = int(request.form.get('year'))
        basic_salary = float(request.form.get('basic_salary', 0))
        hra = float(request.form.get('hra', 0))
        da = float(request.form.get('da', 0))
        allowances = float(request.form.get('allowances', 0))
        tax = float(request.form.get('tax', 0))
        pf = float(request.form.get('pf', 0))
        deductions = float(request.form.get('deductions', 0))
        payment_date_str = request.form.get('payment_date')
        remarks = request.form.get('remarks')

        existing = Payroll.query.filter_by(
            employee_id=employee_id, month=month, year=year
        ).first()
        if existing:
            flash('Payroll already exists for this employee for the selected month!', 'danger')
            return render_template('generate_payroll.html', employees=employees)

        total_deductions = deductions + tax + pf
        net_salary = basic_salary + hra + da + allowances - total_deductions

        payroll = Payroll(
            employee_id=employee_id,
            month=month,
            year=year,
            basic_salary=basic_salary,
            hra=hra,
            da=da,
            allowances=allowances,
            tax=tax,
            pf=pf,
            deductions=deductions,
            net_salary=net_salary,
            payment_date=datetime.strptime(payment_date_str, '%Y-%m-%d').date() if payment_date_str else date.today(),
            status='generated',
            remarks=remarks
        )
        db.session.add(payroll)
        db.session.commit()
        flash('Payroll generated successfully!', 'success')
        return redirect(url_for('payroll.list_payroll'))

    return render_template('generate_payroll.html', employees=employees)


@payroll_bp.route('/view/<int:id>')
@login_required
def view_payroll(id):
    payroll = Payroll.query.get_or_404(id)

    if current_user.role == 'employee':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        if not emp or payroll.employee_id != emp.id:
            abort(403)
    elif current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids and payroll.employee_id not in team_ids:
            abort(403)

    return render_template('view_payroll.html', payroll=payroll)


@payroll_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_payroll(id):
    if not can_manage_payroll(current_user):
        abort(403)
    payroll = Payroll.query.get_or_404(id)
    db.session.delete(payroll)
    db.session.commit()
    flash('Payroll record deleted!', 'success')
    return redirect(url_for('payroll.list_payroll'))


@payroll_bp.route('/process/<int:id>')
@login_required
def process_payroll(id):
    if not can_manage_payroll(current_user):
        abort(403)
    payroll = Payroll.query.get_or_404(id)
    payroll.status = 'processed'
    db.session.commit()
    flash('Payroll processed successfully!', 'success')
    return redirect(url_for('payroll.list_payroll'))


@payroll_bp.route('/api/employee-salary/<int:employee_id>')
@login_required
def get_employee_salary(employee_id):
    if current_user.role == 'employee':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        if not emp or emp.id != employee_id:
            abort(403)

    employee = Employee.query.get_or_404(employee_id)
    return jsonify({
        'salary': employee.salary,
        'name': f'{employee.first_name} {employee.last_name}',
        'code': employee.employee_code
    })
