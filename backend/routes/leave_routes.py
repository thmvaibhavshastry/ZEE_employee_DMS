from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from models import db, Leave, Employee
from datetime import datetime, date
from rbac import get_team_employee_ids, can_approve_leave

leave_bp = Blueprint('leave', __name__, url_prefix='/leave')


@leave_bp.route('/')
@login_required
def list_leaves():
    if current_user.role == 'employee':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        if emp:
            leaves = Leave.query.filter_by(employee_id=emp.id).order_by(Leave.created_at.desc()).all()
        else:
            leaves = []
    elif current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids:
            leaves = Leave.query.filter(
                Leave.employee_id.in_(team_ids)
            ).order_by(Leave.created_at.desc()).all()
        else:
            leaves = []
    else:
        leaves = Leave.query.order_by(Leave.created_at.desc()).all()

    return render_template('leaves.html', leaves=leaves)


@leave_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply_leave():
    if current_user.role == 'employee':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        employees = [emp] if emp else []
    elif current_user.role == 'manager':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        team = Employee.query.filter(
            Employee.reporting_manager_id == emp.id
        ).all() if emp else []
        employees = team + ([emp] if emp else [])
    else:
        employees = Employee.query.all()

    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        leave_type = request.form.get('leave_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason')

        if current_user.role == 'employee':
            emp = Employee.query.filter_by(user_id=current_user.id).first()
            if emp and int(employee_id) != emp.id:
                abort(403)
        elif current_user.role == 'manager':
            team_ids = get_team_employee_ids(current_user)
            if team_ids and int(employee_id) not in team_ids:
                abort(403)

        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        leave = Leave(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start,
            end_date=end,
            reason=reason,
            status='pending'
        )
        db.session.add(leave)
        db.session.commit()
        flash('Leave application submitted!', 'success')
        return redirect(url_for('leave.list_leaves'))

    return render_template('apply_leave.html', employees=employees, today=date.today())


@leave_bp.route('/approve/<int:id>')
@login_required
def approve_leave(id):
    if not can_approve_leave(current_user):
        abort(403)

    leave = Leave.query.get_or_404(id)

    if current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids and leave.employee_id not in team_ids:
            abort(403)

    leave.status = 'approved'
    my_emp = Employee.query.filter_by(user_id=current_user.id).first()
    leave.approved_by = my_emp.id if my_emp else None
    leave.approved_at = datetime.utcnow()
    db.session.commit()
    flash('Leave approved!', 'success')
    return redirect(url_for('leave.list_leaves'))


@leave_bp.route('/reject/<int:id>')
@login_required
def reject_leave(id):
    if not can_approve_leave(current_user):
        abort(403)

    leave = Leave.query.get_or_404(id)

    if current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids and leave.employee_id not in team_ids:
            abort(403)

    leave.status = 'rejected'
    my_emp = Employee.query.filter_by(user_id=current_user.id).first()
    leave.approved_by = my_emp.id if my_emp else None
    leave.approved_at = datetime.utcnow()
    db.session.commit()
    flash('Leave rejected!', 'success')
    return redirect(url_for('leave.list_leaves'))


@leave_bp.route('/api/employee-leaves/<int:employee_id>')
@login_required
def get_employee_leaves(employee_id):
    if current_user.role == 'employee':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        if not emp or emp.id != employee_id:
            abort(403)
    elif current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids and employee_id not in team_ids:
            abort(403)

    year = request.args.get('year', date.today().year)
    leaves = Leave.query.filter(
        Leave.employee_id == employee_id,
        db.extract('year', Leave.start_date) == int(year)
    ).all()

    sick_leaves = sum(
        (l.end_date - l.start_date).days + 1
        for l in leaves if l.leave_type == 'sick' and l.status == 'approved'
    )
    earned_leaves = sum(
        (l.end_date - l.start_date).days + 1
        for l in leaves if l.leave_type == 'earned' and l.status == 'approved'
    )

    return jsonify({
        'sick_leaves_taken': sick_leaves,
        'earned_leaves_taken': earned_leaves,
        'total_sick_entitled': 12,
        'total_earned_entitled': 18,
        'sick_remaining': max(0, 12 - sick_leaves),
        'earned_remaining': max(0, 18 - earned_leaves)
    })
