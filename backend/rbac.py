from flask import abort, render_template
from flask_login import current_user
from functools import wraps
from models import Employee, Manager, Attendance, Leave


ROLES_HIERARCHY = {
    'superadmin': 4,
    'admin': 3,
    'manager': 2,
    'employee': 1,
}


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def min_role_required(min_role):
    min_level = ROLES_HIERARCHY.get(min_role, 0)
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            user_level = ROLES_HIERARCHY.get(current_user.role, 0)
            if user_level < min_level:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_team_employee_ids(user):
    if user.role == 'superadmin' or user.role == 'admin':
        return None
    if user.role == 'manager':
        emp = Employee.query.filter_by(user_id=user.id).first()
        if emp:
            team = Employee.query.filter_by(reporting_manager_id=emp.id).all()
            return [e.id for e in team] + [emp.id]
        return []
    if user.role == 'employee':
        emp = Employee.query.filter_by(user_id=user.id).first()
        return [emp.id] if emp else []
    return []


def can_access_employee(user, employee):
    if user.role in ('superadmin', 'admin'):
        return True
    if user.role == 'manager':
        team_ids = get_team_employee_ids(user)
        return employee.id in team_ids if team_ids else False
    if user.role == 'employee':
        emp = Employee.query.filter_by(user_id=user.id).first()
        return emp.id == employee.id if emp else False
    return False


def can_manage_leave(user, leave):
    if user.role in ('superadmin', 'admin'):
        return True
    if user.role == 'manager':
        team_ids = get_team_employee_ids(user)
        return leave.employee_id in team_ids if team_ids else False
    if user.role == 'employee':
        return leave.employee_id == (lambda e: e.id if e else None)(Employee.query.filter_by(user_id=user.id).first())
    return False


def can_approve_leave(user):
    return user.role in ('superadmin', 'admin', 'manager')


def can_manage_payroll(user):
    return user.role in ('superadmin', 'admin')


def can_manage_holidays(user):
    return user.role in ('superadmin', 'admin')


def can_manage_managers(user):
    return user.role in ('superadmin', 'admin')


def can_manage_admins(user):
    return user.role == 'superadmin'


def get_employee_for_user(user):
    if user.role in ('superadmin', 'admin'):
        return None
    return Employee.query.filter_by(user_id=user.id).first()
