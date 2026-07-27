from flask import Flask, render_template
from flask_login import LoginManager, current_user
from config import Config
from models import db, User, Employee
from datetime import datetime


def create_app():
    app = Flask(
        __name__,
        template_folder='../frontend/templates',
        static_folder='../frontend/static'
    )
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('access_denied.html'), 403

    @app.context_processor
    def inject_now():
        return {'now': datetime.now}

    @app.context_processor
    def inject_role_helpers():
        from rbac import (
            ROLES_HIERARCHY, get_team_employee_ids,
            can_manage_managers, can_manage_admins,
            can_manage_payroll, can_manage_holidays,
            can_approve_leave, get_employee_for_user
        )

        def is_superadmin():
            return current_user.is_authenticated and current_user.role == 'superadmin'

        def is_admin():
            return current_user.is_authenticated and current_user.role == 'admin'

        def is_manager():
            return current_user.is_authenticated and current_user.role == 'manager'

        def is_employee():
            return current_user.is_authenticated and current_user.role == 'employee'

        def is_manager_or_above():
            return current_user.is_authenticated and ROLES_HIERARCHY.get(current_user.role, 0) >= 2

        def is_admin_or_above():
            return current_user.is_authenticated and ROLES_HIERARCHY.get(current_user.role, 0) >= 3

        def get_managed_employees():
            if not current_user.is_authenticated:
                return []
            emp = Employee.query.filter_by(user_id=current_user.id).first()
            if emp:
                return Employee.query.filter_by(reporting_manager_id=emp.id).all()
            return []

        def get_my_employee_profile():
            if not current_user.is_authenticated:
                return None
            return Employee.query.filter_by(user_id=current_user.id).first()

        return {
            'is_superadmin': is_superadmin,
            'is_admin': is_admin,
            'is_manager': is_manager,
            'is_employee': is_employee,
            'is_manager_or_above': is_manager_or_above,
            'is_admin_or_above': is_admin_or_above,
            'can_manage_managers': can_manage_managers(current_user) if current_user.is_authenticated else False,
            'can_manage_admins': can_manage_admins(current_user) if current_user.is_authenticated else False,
            'can_manage_payroll': can_manage_payroll(current_user) if current_user.is_authenticated else False,
            'can_manage_holidays': can_manage_holidays(current_user) if current_user.is_authenticated else False,
            'can_approve_leave': can_approve_leave(current_user) if current_user.is_authenticated else False,
            'get_managed_employees': get_managed_employees,
            'get_my_employee_profile': get_my_employee_profile,
        }

    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.employee_routes import emp_bp
    from routes.manager_routes import mgr_bp
    from routes.payroll_routes import payroll_bp
    from routes.attendance_routes import att_bp
    from routes.leave_routes import leave_bp
    from routes.holiday_routes import holiday_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(emp_bp)
    app.register_blueprint(mgr_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(att_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(holiday_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
