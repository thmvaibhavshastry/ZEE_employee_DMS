from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, Employee, User, Manager
from datetime import datetime
from rbac import role_required, get_team_employee_ids, can_access_employee

emp_bp = Blueprint('employees', __name__, url_prefix='/employees')


@emp_bp.route('/')
@login_required
def list_employees():
    if current_user.role == 'employee':
        abort(403)

    if current_user.role == 'manager':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        if emp:
            employees = Employee.query.filter(
                Employee.reporting_manager_id == emp.id
            ).order_by(Employee.first_name).all()
        else:
            employees = []
    else:
        employees = Employee.query.order_by(Employee.first_name).all()

    return render_template('employees.html', employees=employees)


@emp_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if current_user.role == 'employee':
        abort(403)

    if current_user.role == 'manager':
        my_emp = Employee.query.filter_by(user_id=current_user.id).first()
        managers = [my_emp] if my_emp else []
    else:
        managers = Employee.query.filter(Employee.reporting_manager_id.is_(None)).all()
    all_employees = Employee.query.all()

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        designation = request.form.get('designation')
        salary = request.form.get('salary', 0)
        date_of_joining = request.form.get('date_of_joining')
        date_of_birth = request.form.get('date_of_birth')
        address = request.form.get('address')
        reporting_manager_id = request.form.get('reporting_manager_id')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'danger')
            return render_template('add_employee.html', managers=managers, all_employees=all_employees)

        existing_email_user = User.query.filter_by(email=email).first()
        if existing_email_user:
            flash('Email already exists!', 'danger')
            return render_template('add_employee.html', managers=managers, all_employees=all_employees)

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='employee'
        )
        db.session.add(user)
        db.session.flush()

        last_emp = Employee.query.order_by(Employee.id.desc()).first()
        if last_emp and last_emp.employee_code and last_emp.employee_code.startswith('EMP'):
            last_num = int(last_emp.employee_code[3:])
            next_code = last_num + 1
        else:
            next_code = 1
        employee_code = f'EMP{next_code:04d}'

        employee = Employee(
            user_id=user.id,
            employee_code=employee_code,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            department=department,
            designation=designation,
            salary=float(salary) if salary else 0,
            date_of_joining=datetime.strptime(date_of_joining, '%Y-%m-%d').date() if date_of_joining else None,
            date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None,
            address=address,
            reporting_manager_id=int(reporting_manager_id) if reporting_manager_id and reporting_manager_id != '' else None
        )
        db.session.add(employee)
        db.session.commit()

        flash('Employee added successfully!', 'success')
        return redirect(url_for('employees.list_employees'))

    return render_template('add_employee.html', managers=managers, all_employees=all_employees)


@emp_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    if not can_access_employee(current_user, employee):
        abort(403)

    if current_user.role == 'manager':
        my_emp = Employee.query.filter_by(user_id=current_user.id).first()
        managers = [my_emp] if my_emp else []
    else:
        managers = Employee.query.filter(Employee.reporting_manager_id.is_(None), Employee.id != id).all()
    all_employees = Employee.query.filter(Employee.id != id).all()

    if request.method == 'POST':
        employee.first_name = request.form.get('first_name')
        employee.last_name = request.form.get('last_name')
        employee.email = request.form.get('email')
        employee.phone = request.form.get('phone')
        employee.department = request.form.get('department')
        employee.designation = request.form.get('designation')
        employee.salary = float(request.form.get('salary', 0))

        dob = request.form.get('date_of_birth')
        if dob:
            employee.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()

        doj = request.form.get('date_of_joining')
        if doj:
            employee.date_of_joining = datetime.strptime(doj, '%Y-%m-%d').date()

        employee.address = request.form.get('address')

        mgr_id = request.form.get('reporting_manager_id')
        employee.reporting_manager_id = int(mgr_id) if mgr_id and mgr_id != '' else None

        db.session.commit()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('employees.list_employees'))

    return render_template('edit_employee.html', employee=employee, managers=managers, all_employees=all_employees)


@emp_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    if not can_access_employee(current_user, employee):
        abort(403)

    Employee.query.filter_by(reporting_manager_id=id).update({Employee.reporting_manager_id: None})

    user = User.query.get(employee.user_id)
    if user:
        db.session.delete(user)

    db.session.delete(employee)
    db.session.commit()
    flash('Employee deleted successfully!', 'success')
    return redirect(url_for('employees.list_employees'))


@emp_bp.route('/view/<int:id>')
@login_required
def view_employee(id):
    employee = Employee.query.get_or_404(id)
    if current_user.role == 'employee':
        my_emp = Employee.query.filter_by(user_id=current_user.id).first()
        if not my_emp or my_emp.id != employee.id:
            abort(403)
    elif current_user.role == 'manager':
        if not can_access_employee(current_user, employee):
            abort(403)
    return render_template('view_employee.html', employee=employee)


@emp_bp.route('/api/reportees/<int:manager_id>')
@login_required
def get_reportees(manager_id):
    if current_user.role == 'employee':
        abort(403)
    reportees = Employee.query.filter_by(reporting_manager_id=manager_id).all()
    return jsonify([{
        'id': e.id,
        'name': f'{e.first_name} {e.last_name}',
        'department': e.department,
        'designation': e.designation
    } for e in reportees])
