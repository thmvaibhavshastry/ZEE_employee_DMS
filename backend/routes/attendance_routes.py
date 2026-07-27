from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from models import db, Attendance, Employee
from datetime import datetime, date
from rbac import get_team_employee_ids

att_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@att_bp.route('/')
@login_required
def list_attendance():
    today = date.today()

    if current_user.role == 'employee':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        if emp:
            records = Attendance.query.filter_by(employee_id=emp.id, date=today).all()
        else:
            records = []
    elif current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids:
            records = Attendance.query.filter(
                Attendance.employee_id.in_(team_ids),
                Attendance.date == today
            ).order_by(Attendance.employee_id).all()
        else:
            records = []
    else:
        records = Attendance.query.filter_by(date=today).order_by(Attendance.employee_id).all()

    return render_template('attendance.html', records=records, today=today)


@att_bp.route('/mark', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    if current_user.role == 'employee':
        abort(403)

    if current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids:
            employees = Employee.query.filter(Employee.id.in_(team_ids)).all()
        else:
            employees = []
    else:
        employees = Employee.query.all()

    if request.method == 'POST':
        attendance_date_str = request.form.get('date')
        attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()

        existing = Attendance.query.filter_by(date=attendance_date).first()
        if existing:
            flash(f'Attendance already marked for {attendance_date_str}. Use update option.', 'warning')
            return redirect(url_for('attendance.list_attendance'))

        employee_ids = request.form.getlist('employee_id[]')
        statuses = request.form.getlist('status[]')
        check_ins = request.form.getlist('check_in[]')
        check_outs = request.form.getlist('check_out[]')
        remarks_list = request.form.getlist('remarks[]')

        for i, emp_id in enumerate(employee_ids):
            att = Attendance(
                employee_id=int(emp_id),
                date=attendance_date,
                status=statuses[i] if i < len(statuses) else 'absent',
                check_in=check_ins[i] if i < len(check_ins) else None,
                check_out=check_outs[i] if i < len(check_outs) else None,
                remarks=remarks_list[i] if i < len(remarks_list) else None
            )
            db.session.add(att)

        db.session.commit()
        flash(f'Attendance marked for {attendance_date_str}!', 'success')
        return redirect(url_for('attendance.list_attendance'))

    return render_template('mark_attendance.html', employees=employees, today=date.today())


@att_bp.route('/report')
@login_required
def attendance_report():
    if current_user.role == 'employee':
        abort(403)

    if current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids:
            employees = Employee.query.filter(Employee.id.in_(team_ids)).all()
        else:
            employees = []
    else:
        employees = Employee.query.all()

    return render_template('attendance_report.html', employees=employees)


@att_bp.route('/api/report')
@login_required
def api_attendance_report():
    if current_user.role == 'employee':
        abort(403)

    emp_id = request.args.get('employee_id')
    month = request.args.get('month', date.today().month)
    year = request.args.get('year', date.today().year)

    query = Attendance.query.filter(
        db.extract('month', Attendance.date) == int(month),
        db.extract('year', Attendance.date) == int(year)
    )

    if current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids:
            query = query.filter(Attendance.employee_id.in_(team_ids))
        else:
            return jsonify([])

    if emp_id:
        if current_user.role == 'manager':
            team_ids = get_team_employee_ids(current_user)
            if team_ids and int(emp_id) not in team_ids:
                return jsonify([])
        query = query.filter_by(employee_id=int(emp_id))

    records = query.order_by(Attendance.date).all()

    return jsonify([{
        'id': r.id,
        'employee_name': f'{r.employee.first_name} {r.employee.last_name}',
        'date': r.date.strftime('%Y-%m-%d'),
        'status': r.status,
        'check_in': r.check_in,
        'check_out': r.check_out,
        'remarks': r.remarks
    } for r in records])


@att_bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update_attendance(id):
    if current_user.role == 'employee':
        abort(403)

    record = Attendance.query.get_or_404(id)

    if current_user.role == 'manager':
        team_ids = get_team_employee_ids(current_user)
        if team_ids and record.employee_id not in team_ids:
            abort(403)

    if request.method == 'POST':
        record.status = request.form.get('status')
        record.check_in = request.form.get('check_in')
        record.check_out = request.form.get('check_out')
        record.remarks = request.form.get('remarks')
        db.session.commit()
        flash('Attendance updated!', 'success')
        return redirect(url_for('attendance.list_attendance'))

    return render_template('update_attendance.html', record=record)
