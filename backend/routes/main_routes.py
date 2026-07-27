from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Employee, Payroll, Attendance, Leave, Holiday
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
from rbac import get_team_employee_ids

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def dashboard():
    today = date.today()
    current_year = today.year
    current_month = today.month

    if current_user.role == 'employee':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        if emp:
            my_att = Attendance.query.filter_by(employee_id=emp.id, date=today).first()
            my_pending_leaves = Leave.query.filter_by(employee_id=emp.id, status='pending').count()
            my_approved_leaves = Leave.query.filter_by(employee_id=emp.id, status='approved').count()
            my_payroll = Payroll.query.filter_by(employee_id=emp.id).order_by(
                Payroll.year.desc(), Payroll.month.desc()
            ).first()
        else:
            my_att = None
            my_pending_leaves = 0
            my_approved_leaves = 0
            my_payroll = None

        return render_template('dashboard.html',
            my_employee=emp,
            my_attendance=my_att,
            my_pending_leaves=my_pending_leaves,
            my_approved_leaves=my_approved_leaves,
            my_payroll=my_payroll,
            today=today,
        )

    if current_user.role == 'manager':
        emp = Employee.query.filter_by(user_id=current_user.id).first()
        team_ids = get_team_employee_ids(current_user)

        total_employees = len(team_ids) - 1 if team_ids and emp else 0
        present_today = Attendance.query.filter(
            Attendance.employee_id.in_(team_ids),
            Attendance.date == today,
            Attendance.status == 'present'
        ).count() if team_ids else 0
        late_today = Attendance.query.filter(
            Attendance.employee_id.in_(team_ids),
            Attendance.date == today,
            Attendance.status == 'late'
        ).count() if team_ids else 0
        absent_today = Attendance.query.filter(
            Attendance.employee_id.in_(team_ids),
            Attendance.date == today,
            Attendance.status == 'absent'
        ).count() if team_ids else 0
        pending_leaves = Leave.query.filter(
            Leave.employee_id.in_(team_ids),
            Leave.status == 'pending'
        ).count() if team_ids else 0

        employees_on_leave = Leave.query.filter(
            Leave.employee_id.in_(team_ids),
            Leave.start_date <= today,
            Leave.end_date >= today,
            Leave.status == 'approved'
        ).all() if team_ids else []

        team_members = Employee.query.filter(
            Employee.id.in_(team_ids),
            Employee.id != (emp.id if emp else 0)
        ).all() if team_ids else []

        return render_template('dashboard.html',
            total_employees=total_employees,
            present_today=present_today,
            late_today=late_today,
            absent_today=absent_today,
            pending_leaves=pending_leaves,
            employees_on_leave=employees_on_leave,
            team_members=team_members,
            today=today,
        )

    total_employees = Employee.query.count()
    new_joined = Employee.query.filter(
        extract('year', Employee.date_of_joining) == current_year
    ).count()
    resigned_count = 0

    present_today = Attendance.query.filter_by(date=today, status='present').count()
    late_today = Attendance.query.filter_by(date=today, status='late').count()
    absent_today = Attendance.query.filter_by(date=today, status='absent').count()

    employees_on_leave_today = Leave.query.filter(
        Leave.start_date <= today,
        Leave.end_date >= today,
        Leave.status == 'approved'
    ).all()

    today_events = [
        {'title': 'Team Standup', 'time': '10:00 AM', 'type': 'meeting'},
        {'title': 'Sprint Review', 'time': '2:00 PM', 'type': 'meeting'},
    ]

    birthday_today = Employee.query.filter(
        extract('month', Employee.date_of_birth) == current_month,
        extract('day', Employee.date_of_birth) == today.day
    ).first()
    if birthday_today:
        today_events.insert(0, {
            'title': f'{birthday_today.first_name}\'s Birthday',
            'type': 'birthday'
        })

    job_applied_data = [
        {'month': 'Jan', 'count': 45},
        {'month': 'Feb', 'count': 52},
        {'month': 'Mar', 'count': 38},
        {'month': 'Apr', 'count': 65},
        {'month': 'May', 'count': 48},
        {'month': 'Jun', 'count': 72},
        {'month': 'Jul', 'count': 30},
    ]

    active_month_idx = current_month - 1
    for i, d in enumerate(job_applied_data):
        d['active'] = (i == active_month_idx)

    projects = {
        'total': 50,
        'signed': 22,
        'manager_review': 16,
        'client_review': 12,
    }

    performance_table = [
        {'name': 'Amit Sharma', 'age': 28, 'dept': 'Engineering', 'projects': 5, 'salary': 75000},
        {'name': 'Priya Patel', 'age': 32, 'dept': 'Engineering', 'projects': 8, 'salary': 95000},
        {'name': 'Rajesh Kumar', 'age': 35, 'dept': 'Engineering', 'projects': 12, 'salary': 120000},
        {'name': 'Sneha Reddy', 'age': 26, 'dept': 'Marketing', 'projects': 4, 'salary': 55000},
        {'name': 'Vikram Singh', 'age': 30, 'dept': 'Sales', 'projects': 6, 'salary': 65000},
    ]

    dept_distribution = db.session.query(
        Employee.department,
        func.count(Employee.id).label('count')
    ).filter(
        Employee.department.isnot(None)
    ).group_by(Employee.department).all()

    dept_names = [r.department for r in dept_distribution]
    dept_data = [r.count for r in dept_distribution]

    employee_types = {
        'full_time': int(total_employees * 0.68),
        'part_time': int(total_employees * 0.20),
        'internship': int(total_employees * 0.12),
    }

    performance_trend = {
        'year1': 2021,
        'year2': 2022,
        'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'year1_data': [65, 59, 80, 81, 56, 55, 72, 68, 74, 78, 82, 88],
        'year2_data': [78, 72, 85, 92, 78, 82, 90, 88, 92, 95, 96, 98],
    }

    up_holidays = Holiday.query.filter(Holiday.date >= today).order_by(Holiday.date).limit(5).all()

    return render_template('dashboard.html',
        total_employees=total_employees,
        new_joined=new_joined,
        resigned_count=resigned_count,
        present_today=present_today,
        late_today=late_today,
        absent_today=absent_today,
        employees_on_leave=employees_on_leave_today,
        today_events=today_events,
        job_applied_data=job_applied_data,
        projects=projects,
        performance_table=performance_table,
        dept_names=dept_names,
        dept_data=dept_data,
        employee_types=employee_types,
        performance_trend=performance_trend,
        up_holidays=up_holidays,
        today=today
    )
