from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, Manager, User, Employee
from datetime import datetime
from rbac import role_required

mgr_bp = Blueprint('managers', __name__, url_prefix='/managers')


@mgr_bp.route('/')
@login_required
def list_managers():
    if current_user.role not in ('superadmin', 'admin'):
        abort(403)
    managers = Manager.query.order_by(Manager.first_name).all()
    return render_template('managers.html', managers=managers)


@mgr_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_manager():
    if current_user.role not in ('superadmin', 'admin'):
        abort(403)

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        designation = request.form.get('designation')
        date_of_joining = request.form.get('date_of_joining')
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return render_template('add_manager.html')

        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return render_template('add_manager.html')

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='manager'
        )
        db.session.add(user)
        db.session.flush()

        mgr_count = Manager.query.count() + 1
        manager_code = f'MGR{mgr_count:04d}'

        manager = Manager(
            user_id=user.id,
            manager_code=manager_code,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            department=department,
            designation=designation,
            date_of_joining=datetime.strptime(date_of_joining, '%Y-%m-%d').date() if date_of_joining else None,
            created_by_admin_id=current_user.id
        )
        db.session.add(manager)
        db.session.commit()

        flash('Manager added successfully!', 'success')
        return redirect(url_for('managers.list_managers'))

    return render_template('add_manager.html')


@mgr_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_manager(id):
    if current_user.role not in ('superadmin', 'admin'):
        abort(403)

    manager = Manager.query.get_or_404(id)

    if current_user.role == 'admin' and manager.created_by_admin_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        manager.first_name = request.form.get('first_name')
        manager.last_name = request.form.get('last_name')
        manager.email = request.form.get('email')
        manager.phone = request.form.get('phone')
        manager.department = request.form.get('department')
        manager.designation = request.form.get('designation')

        doj = request.form.get('date_of_joining')
        if doj:
            manager.date_of_joining = datetime.strptime(doj, '%Y-%m-%d').date()

        db.session.commit()
        flash('Manager updated successfully!', 'success')
        return redirect(url_for('managers.list_managers'))

    return render_template('edit_manager.html', manager=manager)


@mgr_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_manager(id):
    if current_user.role not in ('superadmin', 'admin'):
        abort(403)

    manager = Manager.query.get_or_404(id)

    if current_user.role == 'admin' and manager.created_by_admin_id != current_user.id:
        abort(403)

    user = User.query.get(manager.user_id)
    if user:
        db.session.delete(user)
    db.session.delete(manager)
    db.session.commit()
    flash('Manager deleted successfully!', 'success')
    return redirect(url_for('managers.list_managers'))


@mgr_bp.route('/view/<int:id>')
@login_required
def view_manager(id):
    if current_user.role not in ('superadmin', 'admin'):
        abort(403)

    manager = Manager.query.get_or_404(id)
    reportees = Employee.query.filter_by(reporting_manager_id=id).all()
    return render_template('view_manager.html', manager=manager, reportees=reportees)


@mgr_bp.route('/api/managers')
@login_required
def get_managers_api():
    if current_user.role == 'employee':
        abort(403)
    managers = Manager.query.all()
    return jsonify([{
        'id': m.id,
        'name': f'{m.first_name} {m.last_name}',
        'code': m.manager_code,
        'department': m.department
    } for m in managers])
